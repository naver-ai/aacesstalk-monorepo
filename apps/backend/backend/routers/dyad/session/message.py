import asyncio
from typing import Annotated

import aiofiles
from py_core.utils.speech.speech_recognizer_base import SpeechRecognizerBase
from py_core.utils.speech.whisper import WhisperSpeechRecognizer
from pydantic import BaseModel
from os import path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Response
from py_core import ModeratorSession
from chatlib.utils.time import get_timestamp
from py_core.system.model import Dialogue, ParentGuideRecommendationResult, CardIdentity, ChildCardRecommendationResult, \
    CardInfo, ParentExampleMessage, UserLocale

from py_core.system.task.parent_guide_recommendation.punctuator import Punctuator

from py_core.config import AACessTalkConfig

from py_core.utils.speech import ClovaLongSpeech

from backend.routers.dyad.common import get_signed_in_dyad_orm, retrieve_moderator_session

from typing import TypeVar, Generic

from backend.routers.errors import ErrorType
from py_database.model import DyadORM

T = TypeVar('T')

class ResponseWithTurnId(BaseModel, Generic[T]):
    payload: T
    next_turn_id: str

router = APIRouter()


clova_asr: SpeechRecognizerBase = ClovaLongSpeech()
whisper_asr: SpeechRecognizerBase = WhisperSpeechRecognizer()

punctuator = Punctuator()

class DialogueResponse(BaseModel):
    dyad_id: str
    dialogue: Dialogue

@router.get("/all", response_model=DialogueResponse)
async def get_dialogue(dyad: Annotated[DyadORM, Depends(get_signed_in_dyad_orm)], session: Annotated[ModeratorSession, Depends(retrieve_moderator_session)]) -> DialogueResponse:
    dialogue = await session.storage.get_dialogue()
    return DialogueResponse(dyad_id=dyad.id, dialogue=dialogue)


class SendParentMessageArgs(BaseModel):
    message: str

@router.post("/parent/message/text", response_model=ResponseWithTurnId[ChildCardRecommendationResult])
async def send_parent_message_text(args: SendParentMessageArgs,
                              session: Annotated[ModeratorSession, Depends(retrieve_moderator_session)]) -> ResponseWithTurnId[ChildCardRecommendationResult]:
    turn, recommendation = await session.submit_parent_message(parent_message=args.message)
    return ResponseWithTurnId(payload=recommendation, next_turn_id=turn.id)



@router.post('/parent/message/audio')
async def send_parent_message_audio(file: Annotated[UploadFile, File()], turn_id: Annotated[str, Form()], 
                                    dyad: Annotated[DyadORM, Depends(get_signed_in_dyad_orm)],
                                    session_id: str, session: Annotated[ModeratorSession, Depends(retrieve_moderator_session)]) -> ResponseWithTurnId[ChildCardRecommendationResult]:
    try:
        print("Dictate parent turn audio...")

        extension = file.filename.split(".")[-1]
        target_filename = f"{session_id}__{turn_id}__{get_timestamp()}.{extension}"
        target_file_path = path.join(AACessTalkConfig.get_turn_audio_recording_dir_path(dyad.id, make_if_not_exist=True), 
                                         target_filename)

        async def write_file_task():
            
            async with aiofiles.open(target_file_path, 'wb') as tf:
                while content := await file.read(1024):
                    await tf.write(content)

        async def write_turn_info():
            turn_info = await session.storage.get_latest_turn()
            turn_info.audio_filename = target_filename
            await session.storage.upsert_dialogue_turn(turn_info)

        
        await asyncio.gather(write_file_task(), write_turn_info())

        asr_engine = clova_asr if dyad.locale == UserLocale.Korean and ClovaLongSpeech.assert_authorize() else whisper_asr

        text = await asr_engine.recognize_speech(file.filename, open(target_file_path, 'rb'), file.content_type, dyad.locale, dyad.child_name)
        if len(text) > 0:
            processed_text = await punctuator.punctuate(text)
            print(text, processed_text)
            # Generate recommendation
            turn, recommendation = await session.submit_parent_message(parent_message=processed_text)
            return ResponseWithTurnId(payload=recommendation, next_turn_id=turn.id)
        else:
            return Response(status_code=500, content=ErrorType.EmptyDictation)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=ex.__str__()) from ex

class RequestExampleArgs(BaseModel):
    recommendation_id: str
    guide_id: str

@router.post("/parent/example", response_model=ParentExampleMessage)
async def request_example_message(
    args: RequestExampleArgs, session: Annotated[ModeratorSession, Depends(retrieve_moderator_session)]) -> ParentExampleMessage:
    return await session.request_parent_example_message(**args.model_dump())


class CardSelectionResult(BaseModel):
    interim_cards: list[CardInfo]
    new_recommendation: ChildCardRecommendationResult


@router.post("/child/add_card", response_model=CardSelectionResult)
async def append_card(card_identity: CardIdentity,
                      session: Annotated[ModeratorSession, Depends(retrieve_moderator_session)]):
    interim_selection = await session.append_child_card(card_identity)
    interim_cards = await session.get_card_info_from_identities(interim_selection.cards)
    new_recommendation = await session.refresh_child_card_recommendation()
    return CardSelectionResult(interim_cards=interim_cards, new_recommendation=new_recommendation)


@router.put("/child/refresh_cards", response_model=ChildCardRecommendationResult)
async def refresh_card_selection(
        session: Annotated[ModeratorSession, Depends(retrieve_moderator_session)]) -> ChildCardRecommendationResult:
    return await session.refresh_child_card_recommendation()

@router.put("/child/pop_last_card", response_model=CardSelectionResult)
async def _pop_last_child_card(
        session: Annotated[ModeratorSession, Depends(retrieve_moderator_session)]) -> CardSelectionResult:
    
    selection, recommendation = await session.pop_last_child_card()
    interim_cards = await session.get_card_info_from_identities(selection.cards)

    return CardSelectionResult(interim_cards=interim_cards, new_recommendation=recommendation)


@router.post("/child/confirm_cards", response_model=ResponseWithTurnId[ParentGuideRecommendationResult])
async def confirm_child_card_selection(
        session: Annotated[ModeratorSession, Depends(retrieve_moderator_session)]) -> ResponseWithTurnId[ParentGuideRecommendationResult]:
    turn, recommendation = await session.confirm_child_card_selection()
    return ResponseWithTurnId[ParentGuideRecommendationResult](next_turn_id=turn.id, payload=recommendation)
