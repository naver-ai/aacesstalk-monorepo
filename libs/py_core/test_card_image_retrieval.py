import questionary
from chatlib.global_config import GlobalConfig
from chatlib.llm.integration.openai_api import GPTChatCompletionAPI
from chatlib.utils.cli import make_non_empty_string_validator

from py_core.system.task.card_image_matching.card_image_db_retriever import CardImageDBRetriever


if __name__ == "__main__":

    print("Test card image retrieval.")
    
    GlobalConfig.is_cli_mode = True
    GPTChatCompletionAPI.assert_authorize()

    retriever = CardImageDBRetriever()


    while True:
        keyword: str = questionary.text("Insert card names in English.", "School, Student, Family", validate=make_non_empty_string_validator("Empty string is not allowed.")).ask()
        cards = retriever.query_nearest_card_image_infos([kw.strip() for kw in keyword.split(",")], k=1)
        print(cards)
