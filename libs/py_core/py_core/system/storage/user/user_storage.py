from abc import ABC, abstractmethod
from os import path, makedirs
from py_core.system.model import FreeTopicDetail, id_generator, UserDefinedCardInfo, CardCategory
from py_core.config import AACessTalkConfig


class UserStorage(ABC):

        
    def __init__(self, user_id: str | None = None):
        self.__user_id = user_id or id_generator()

    @property
    def user_id(self) -> str:
        return self.__user_id

    @abstractmethod
    async def register_user_defined_card(self, info: UserDefinedCardInfo):
        pass

    @abstractmethod
    async def get_user_defined_cards(self) -> list[UserDefinedCardInfo]:
        pass

    @abstractmethod
    async def query_user_defined_card(self, category: CardCategory, label_localized: str)->UserDefinedCardInfo | None:
        pass


    @abstractmethod
    async def get_user_defined_card(self, id: str) -> UserDefinedCardInfo | None:
        pass

    @abstractmethod
    async def remove_user_defined_card(self, id: str):
        pass

    @abstractmethod
    async def upsert_free_topic_detail(self, detail: FreeTopicDetail):
        pass

    @abstractmethod
    async def get_free_topic_details(self)-> list[FreeTopicDetail]:
        pass

    @abstractmethod
    async def get_free_topic_detail(self, id: str) -> FreeTopicDetail | None:
        pass

    @abstractmethod
    async def remove_free_topic_detail(self, id: str):
        pass

    