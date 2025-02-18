from chatlib.utils.jinja_utils import convert_to_jinja_template
from time import perf_counter

from chatlib.tool.converter import generate_pydantic_converter
from chatlib.tool.versatile_mapper import ChatCompletionFewShotMapper, ChatCompletionFewShotMapperParams, \
    MapperInputOutputPair
from chatlib.llm.integration import GPTChatCompletionAPI, ChatGPTModel

from py_core.system.guide_categories import DialogueInspectionCategory
from py_core.system.model import Dialogue, DialogueMessage, DialogueRole, CardCategory
from py_core.system.task.parent_guide_recommendation.common import DialogueInspectionResult
from py_core.system.task.dialogue_conversion import DialogueToStrConversionFunction

_EXAMPLES = [
   MapperInputOutputPair(
         input=[
             DialogueMessage.example_parent_message("What did you do at school?"),
             DialogueMessage.example_child_message(("School", CardCategory.Topic), ("Play", CardCategory.Action)),
             DialogueMessage.example_parent_message("I asked you not to play games at school. Didn't I?")
         ],
         output=DialogueInspectionResult(categories=[DialogueInspectionCategory.Blame], rationale="The parent is about to scold the child not to play games.", feedback="You seem to be scolding him before obtaining to more concrete information. Please gather more information before judgment.")
     ),


   MapperInputOutputPair(
         input=[
             DialogueMessage.example_parent_message("What did you do at school?"),
             DialogueMessage.example_child_message(("Play", CardCategory.Action)),
             DialogueMessage.example_parent_message("You should say, 'I played with my friends at school.'")
         ],
         output=DialogueInspectionResult(categories=[DialogueInspectionCategory.Correction], rationale="The parent is trying to improve the child's response with better sentences or phrases.", feedback="You seem to be correcting the child's response. Please focus more on the topic and context of the conversation.")
       ),


   MapperInputOutputPair(
         input=[
             DialogueMessage.example_parent_message("How are you feeling right now?"),
             DialogueMessage.example_child_message(("Happy", CardCategory.Emotion)),
             DialogueMessage.example_parent_message("What are your plans for today and where are you going to be?")
         ],
         output=DialogueInspectionResult(categories=[DialogueInspectionCategory.Complex], rationale="The parent is confusing the child by asking about both plans and location at once.", feedback="YPlease ask about only one thing to make it easier for the child to answer.")
     ),

    #  MapperInputOutputPair(
    #      input=[
    #          DialogueMessage.example_parent_message("How are you feeling right now?"),
    #          DialogueMessage.example_child_message(("Happy", CardCategory.Emotion)),
    #          DialogueMessage.example_parent_message("What are your plans for today and where are you going to be?"),
    #          DialogueMessage.example_child_message(("Kinder", CardCategory.Topic)),
    #          DialogueMessage.example_parent_message("Where are we going this afternoon?")
    #      ],
    #      output=DialogueInspectionResult(categories=[DialogueInspectionCategory.Complex], rationale="While talking about the events of the day, the parent suddenly asks about the schedule for today.", feedback="Please maintain the general direction of the conversation.")
    #  )
]

_prompt_template = convert_to_jinja_template("""
- Role: You are a helpful communication expert that analyzes a conversation pattern between a parent and a autistic child, and identify noteworthy signals from the parent's behavior responding to his/her child.
- Task: Given a dialogue, inspect the last parent message.

[Input format]
The dialogue will be formatted as an XML.
The last message of the parent to be inspected is marked with an attribute 'inspect="true"'.

[Output format]
- The inspection result would be a JSON object formatted as the following:

{
  "categories": string[] // Inspected category labels as part of the predefined inspection categories in [Inspection categories]. If the inspected message has no issues and no category labels are applicable, just put [].
  "rationale": string | null // Rationale for assigning these inspection categories.
  "feedback": string | null // Provide a message to parents to let them know the current conversation status
}

[Inspection categories]
{%- for category in categories -%}
{%- if (category.min_turns is none) or (category.min_turns <= (dialogue | length)) %}
- "{{category.label}}": {{category.description}}.
{%- endif -%}
{%- endfor -%}""")

def _prompt_generator(input: Dialogue, params: ChatCompletionFewShotMapperParams) -> str:
    prompt = _prompt_template.render(dialogue=input, categories=DialogueInspectionCategory.values_with_desc())
    return prompt


class DialogueInspector:

    def __init__(self):

        str_output_converter, output_str_converter = generate_pydantic_converter(DialogueInspectionResult, 'json')

        self.__mapper: ChatCompletionFewShotMapper[
            Dialogue, DialogueInspectionResult, ChatCompletionFewShotMapperParams] = ChatCompletionFewShotMapper(
            api=GPTChatCompletionAPI(),
            instruction_generator=_prompt_generator,
            input_str_converter=DialogueToStrConversionFunction(message_row_formatter=self.__format_dialogue_row),
            str_output_converter=str_output_converter,
            output_str_converter=output_str_converter
        )

    def __format_dialogue_row(self, formatted: str, message: DialogueMessage, dialogue: Dialogue) -> str:
        index = dialogue.index(message)
        if index == len(dialogue) - 1 and message.role == DialogueRole.Parent:
            return f"\t<msg inspect=\"true\">{formatted}</msg>"
        else:
            return DialogueToStrConversionFunction.message_row_formatter_default(formatted, message, dialogue)

    async def inspect(self, dialogue: Dialogue, task_id: str)->tuple[DialogueInspectionResult | None, str]:
        t_start = perf_counter()
        if len(dialogue) == 0:
            result = None, task_id
        elif dialogue[len(dialogue) - 1].role != DialogueRole.Parent:
            result = None, task_id
        else:
            result = (await self.__mapper.run(_EXAMPLES, dialogue, ChatCompletionFewShotMapperParams(model="gpt-4o-mini", api_params={}))), task_id
            if len(result[0].categories) == 0:
                result = None, task_id
        t_end = perf_counter()
        print(f"Dialogue inspection took {t_end - t_start} sec. result: ", result[0], f"task_id: {result[1]}")

        return result
