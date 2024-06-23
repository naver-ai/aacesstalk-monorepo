from py_core.system.model import CardCategory, UserDefinedCardInfo
from py_core.system.storage import UserStorage


class OnMemoryUserStorage(UserStorage):

    def __init__(self, user_id: str | None):
        super().__init__(user_id)
        self.__user_defined_cards: dict[(str, str), list[UserDefinedCardInfo]] = {}
        self.__user_defined_cards_by_id: dict[str, UserDefinedCardInfo] = {}

    async def register_user_defined_card(self, info: UserDefinedCardInfo):
        if info.id not in self.__user_defined_cards_by_id:
            self.__user_defined_cards_by_id[info.id] = info

            key = (info.category, info.label)
            if key in self.__user_defined_cards and self.__user_defined_cards[key] is not None:
                l = self.__user_defined_cards[key]
                l.append(info)
                l.sort(key=lambda i: i.timestamp, reverse=False)
            else:
                self.__user_defined_cards[key] = [info]

    async def get_user_defined_cards(self) -> list[UserDefinedCardInfo]:
        return [v[len(v) - 1] for k, v in self.__user_defined_cards.items() if v is not None and len(v) >= 1]

    async def query_user_defined_card(self, category: CardCategory, label_localized: str) -> UserDefinedCardInfo | None:
        if (category, label_localized) in self.__user_defined_cards:
            infos = self.__user_defined_cards[(category, label_localized)]
            return infos[len(infos) - 1]
        else:
            return None

    async def get_user_defined_card(self, id: str) -> UserDefinedCardInfo | None:
        return self.__user_defined_cards_by_id[id]

