from functools import cached_property
from typing import Optional

from nanoid import generate
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DictionaryRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: generate(size=10))
    category: str
    english: str
    localized: str
    inspected: bool = False

    @classmethod
    def field_names(cls) -> list[str]:
        return [k for k, v in cls.model_fields.items()]

    @cached_property
    def lookup_key(self) -> tuple[str, str]:
        return self.english, self.category


class CardImageInfo(BaseModel):
    id: str = Field(default_factory=lambda: generate(size=10))
    category: str
    name: str
    filename: str
    format: Optional[str]
    width: int
    height: int
    description: Optional[str] = None
    description_src: Optional[str] = None

    description_brief: Optional[str] = None

    inspected: bool = False
    need_inspection: bool = False

    @field_validator('*')
    @classmethod
    def empty_str_to_none(cls, v: str) -> str | None:
        if isinstance(v, str):
            if len(v) == 0:
                return None
            else:
                return v
        else:
            return v

