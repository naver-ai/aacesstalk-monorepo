import os

import json
from pydantic import BaseModel
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from os import path, makedirs

from py_core.config import AACessTalkConfig
from py_core.system.model import DialogueTurn, Interaction, ParentGuideRecommendationResult, ChildCardRecommendationResult, Dialogue, \
    DialogueMessage, DialogueTypeAdapter, ParentExampleMessage, InterimCardSelection, DialogueRole, SessionInfo
from py_core.system.storage import SessionStorage


class JsonSessionStorage(SessionStorage):


    TABLE_MESSAGES = "messages"
    TABLE_CARD_RECOMMENDATIONS = "card_recommendations"
    TABLE_PARENT_RECOMMENDATIONS = "parent_recommendations"
    TABLE_PARENT_EXAMPLE_MESSAGES = "parent_example_messages"
    TABLE_CARD_SELECTIONS = "card_selections"
    TABLE_CUSTOM_CARD_IMAGES = "custom_care_images"

    TABLE_TURNS = "turns"

    TABLE_INTERACTIONS = "interactions"

    def __init__(self, id: str):
        super().__init__(id)

    @classmethod
    def session_db_dir_path(cls, id: str) -> str:
        dir_path = path.join(AACessTalkConfig.database_dir_path, "json/sessions", id)
        if not path.exists(dir_path):
            makedirs(dir_path)

        return dir_path

    @classmethod
    def session_db_path(cls, id: str) -> str:
        return path.join(cls.session_db_dir_path(id), "db.json")

    @classmethod
    def session_info_path(cls, id: str) -> str:
        return path.join(cls.session_db_dir_path(id), "info.json")


    @classmethod
    async def _load_session_info(cls, session_id: str) -> SessionInfo | None:
        session_info_path = cls.session_info_path(session_id)
        if path.exists(session_info_path):
            with open(session_info_path) as f:
                return SessionInfo(**json.load(f))
        else:
            return None

    async def update_session_info(self, info: SessionInfo):
        session_info_path = self.session_info_path(self.session_id)
        with open(session_info_path, 'w') as f:
            json.dump(info.model_dump(), f)

    @classmethod
    def db(cls, id: str) -> TinyDB:
        return TinyDB(cls.session_db_path(id), CachingMiddleware(JSONStorage))

    def __insert_one(self, table_name: str, model: BaseModel):
        table = self.db(self.session_id).table(table_name)
        table.insert(model.model_dump())

    async def add_dialogue_message(self, message: DialogueMessage):
        self.__insert_one(self.TABLE_MESSAGES, message)

    async def get_dialogue(self) -> Dialogue:
        table = self.db(self.session_id).table(self.TABLE_MESSAGES)
        data = table.all()
        converted = DialogueTypeAdapter.validate_python(data)
        converted.sort(key=lambda m: m.timestamp)
        return converted

    async def add_card_recommendation_result(self, result: ChildCardRecommendationResult):
        self.__insert_one(self.TABLE_CARD_RECOMMENDATIONS, result)

    async def add_parent_guide_recommendation_result(self, result: ParentGuideRecommendationResult):
        self.__insert_one(self.TABLE_PARENT_RECOMMENDATIONS, result)

    async def get_card_recommendation_result(self, recommendation_id: str) -> ChildCardRecommendationResult | None:
        table = self.db(self.session_id).table(self.TABLE_CARD_RECOMMENDATIONS)
        q = Query()
        result = table.search(q.id == recommendation_id)
        if len(result) > 0:
            return ChildCardRecommendationResult(**result[0])
        else:
            return None

    async def get_parent_guide_recommendation_result(self,
                                                     recommendation_id: str) -> ParentGuideRecommendationResult | None:
        table = self.db(self.session_id).table(self.TABLE_PARENT_RECOMMENDATIONS)
        q = Query()
        result = table.search(q.id == recommendation_id)
        if len(result) > 0:
            return ParentGuideRecommendationResult(**result[0])
        else:
            return None

    async def add_parent_example_message(self, message: ParentExampleMessage):
        self.__insert_one(self.TABLE_PARENT_EXAMPLE_MESSAGES, message)

    async def get_parent_example_message(self, recommendation_id: str, guide_id: str) -> ParentExampleMessage | None:
        table = self.db(self.session_id).table(self.TABLE_PARENT_EXAMPLE_MESSAGES)
        q = Query()
        result = table.search((q.recommendation_id == recommendation_id) & (q.guide_id == guide_id))
        if len(result) > 0:
            return ParentExampleMessage(**result[0])
        else:
            return None

    async def __get_latest_model(self, table_name: str, timestamp_column: str = "timestamp", turn_id: str | None = None) -> dict | None:
        table = self.db(self.session_id).table(table_name)

        if turn_id is not None:
            q = Query()
            rows = table.search(q.turn_id == turn_id)
        else:
            rows = table.all()

        sorted_selections = sorted(
                [row for row in rows],
                key=lambda s: s[timestamp_column], reverse=True)
        if len(sorted_selections) > 0:
            return sorted_selections[0]
        else:
            return None

    async def get_latest_card_selection(self, turn_id=None) -> InterimCardSelection | None:
        d = await self.__get_latest_model(self.TABLE_CARD_SELECTIONS, turn_id=turn_id)
        return InterimCardSelection(**d) if d is not None else None

    async def add_card_selection(self, selection: InterimCardSelection):
        self.__insert_one(self.TABLE_CARD_SELECTIONS, selection)

    async def get_latest_parent_guide_recommendation(self, turn_id: str | None = None) -> ParentGuideRecommendationResult | None:
        d = await self.__get_latest_model(self.TABLE_PARENT_RECOMMENDATIONS, turn_id=turn_id)
        return ParentGuideRecommendationResult(**d) if d is not None else None

    async def get_latest_child_card_recommendation(self, turn_id: str | None = None) -> ChildCardRecommendationResult | None:
        d = await self.__get_latest_model(self.TABLE_CARD_RECOMMENDATIONS, turn_id=turn_id)
        return ChildCardRecommendationResult(**d) if d is not None else None

    async def get_latest_dialogue_message(self) -> DialogueMessage | None:
        table = self.db(self.session_id).table(self.TABLE_MESSAGES)
        result = sorted(table.all(), key=lambda m: m["timestamp"], reverse=True)
        if len(result) > 0:
            return DialogueMessage(**result[0])
        else:
            return None


    async def upsert_dialogue_turn(self, turn: DialogueTurn):
        table = self.db(self.session_id).table(self.TABLE_TURNS)

        q = Query()
        result = table.search((q.id == turn.id))
        if len(result) > 0:
            table.update(turn.model_dump(), q.id == turn.id)
        else:
            table.insert(turn.model_dump())

    async def add_interaction(self, interaction: Interaction):
        self.__insert_one(self.TABLE_INTERACTIONS, interaction)


    async def get_latest_turn(self) -> DialogueTurn | None:
        d = await self.__get_latest_model(self.TABLE_TURNS, "started_timestamp")
        return DialogueTurn(**d) if d is not None else None


    async def delete_entities(self):
        os.unlink(self.session_db_dir_path(self.session_id))




