from enum import StrEnum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from sqlmodel import SQLModel, Column, Field, Relationship, JSON
from sqlalchemy import DateTime, func

from py_core.system.model import (id_generator, DialogueRole, DialogueMessage,
                                  CardInfoListTypeAdapter, CardInfo,
                                  ChildCardRecommendationResult,
                                  InterimCardSelection,
                                  ParentGuideRecommendationResult,
                                  ParentGuideElement,
                                  ParentType,
                                  ParentExampleMessage, CardIdentity,
                                  SessionInfo,
                                  DialogueTurn,
                                  Dyad,
                                  InteractionType
                                  )
from py_core.system.session_topic import SessionTopicCategory, SessionTopicInfo
from chatlib.utils.time import get_timestamp


class IdTimestampMixin(BaseModel):
    id: str = Field(primary_key=True, default_factory=id_generator)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs=dict(server_default=func.now(), nullable=True)
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs=dict(server_default=func.now(), onupdate=func.now(), nullable=True)
    )


class DyadORM(SQLModel, IdTimestampMixin, table=True):
    __tablename__: str = "dyad"

    alias: str = Field(min_length=1, unique=True)
    child_name: str = Field(min_length=1)
    parent_type: ParentType = Field(nullable=False)

    sessions: list['SessionORM'] = Relationship(back_populates='dyad')

    def to_data_model(self) -> Dyad:
        return Dyad(id=self.id, alias=self.alias, parent_type=self.parent_type, child_name=self.child_name)


class SessionORM(SQLModel, IdTimestampMixin, table=True):
    __tablename__: str = "session"

    dyad_id: str = Field(foreign_key=f"{DyadORM.__tablename__}.id")

    dyad: DyadORM = Relationship(back_populates="sessions")

    topic_category: SessionTopicCategory
    subtopic: Optional[str] = None
    subtopic_description: Optional[str] = None

    local_timezone: str = Field(nullable=False)
    started_timestamp: int = Field(default_factory=get_timestamp, index=True)
    ended_timestamp: int | None = Field(default=None, index=True)

    def to_data_model(self) -> SessionInfo:
        return SessionInfo(
            id=self.id,
            topic=SessionTopicInfo(category=self.topic_category, subtopic=self.subtopic, subtopic_description=self.subtopic_description),
            local_timezone=self.local_timezone,
            started_timestamp=self.started_timestamp,
            ended=self.ended_timestamp
        )

    @classmethod
    def from_data_model(cls, session_info: SessionInfo, dyad_id: str) -> 'SessionORM':
        return SessionORM(**session_info.model_dump(exclude={'topic'}),
                          dyad_id=dyad_id,
                          topic_category=session_info.topic.category,
                          subtopic=session_info.topic.subtopic,
                          subtopic_description=session_info.topic.subtopic_description
                          )


class SessionIdMixin(BaseModel):
    session_id: str = Field(foreign_key=f"{SessionORM.__tablename__}.id")


class TimestampColumnMixin(BaseModel):
    timestamp: int = Field(default_factory=get_timestamp, index=True)


class DialogueTurnORM(SQLModel, IdTimestampMixin, SessionIdMixin, table=True):
    __tablename__: str = "dialogue_turn"

    session_id: str

    role: DialogueRole

    started_timestamp: int = Field(default_factory=get_timestamp, index=True)
    ended_timestamp: int | None = Field(default=None, index=True)

    @classmethod
    def from_data_model(cls, model: DialogueTurn, session_id: str) -> 'DialogueTurnORM':
        return DialogueTurnORM(**model.model_dump(), session_id=session_id)

    def to_data_model(self) -> DialogueTurn:
        return DialogueTurn(**self.model_dump())

class TurnIdMixin(BaseModel):
    turn_id: str = Field(foreign_key=f"{DialogueTurnORM.__tablename__}.id")

class DialogueMessageContentType(StrEnum):
    text = "text"
    json = "json"

class DialogueMessageORM(SQLModel, IdTimestampMixin, SessionIdMixin, TurnIdMixin, TimestampColumnMixin, table=True):
    __tablename__: str = "message"

    role: DialogueRole
    content_type: DialogueMessageContentType
    content_str_localized: Optional[str] = Field(default=None)
    content_str: str = Field(nullable=False, min_length=1)

    def to_data_model(self) -> DialogueMessage:
        return DialogueMessage(
            id=self.id,
            timestamp=self.timestamp,
            turn_id=self.turn_id,
            role=self.role,
            content=self.content_str if self.content_type == DialogueMessageContentType.text else CardInfoListTypeAdapter.validate_json(
                self.content_str),
            content_localized=self.content_str_localized
        )

    @classmethod
    def from_data_model(cls, session_id: str, message: DialogueMessage) -> 'DialogueMessageORM':
        return DialogueMessageORM(
            **message.model_dump(),
            session_id=session_id,
            content_str_localized=message.content_localized,
            content_str=message.content if isinstance(message.content, str) else CardInfoListTypeAdapter.dump_json(
                message.content),
            content_type=DialogueMessageContentType.text if isinstance(message.content,
                                                                       str) else DialogueMessageContentType.json
        )


class ChildCardRecommendationResultORM(SQLModel, IdTimestampMixin, SessionIdMixin, TurnIdMixin, TimestampColumnMixin, table=True):
    __tablename__: str = "child_card_recommendation_result"

    cards: list[CardInfo] = Field(sa_column=Column(JSON), default=[])

    def to_data_model(self) -> ChildCardRecommendationResult:
        return ChildCardRecommendationResult(**self.model_dump())

    @classmethod
    def from_data_model(cls, session_id: str,
                        data_model: ChildCardRecommendationResult) -> 'ChildCardRecommendationResultORM':
        return ChildCardRecommendationResultORM(**data_model.model_dump(), session_id=session_id)


class InterimCardSelectionORM(SQLModel, IdTimestampMixin, SessionIdMixin, TurnIdMixin, TimestampColumnMixin, table=True):
    __tablename__:str = "interim_card_selection"

    cards: list[CardIdentity] = Field(sa_column=Column(JSON), default=[])

    def to_data_model(self) -> InterimCardSelection:
        return InterimCardSelection(**self.model_dump())

    @classmethod
    def from_data_model(cls, session_id: str, data_model: InterimCardSelection) -> 'InterimCardSelectionORM':
        return InterimCardSelectionORM(**data_model.model_dump(), session_id=session_id)


class ParentGuideRecommendationResultORM(SQLModel, IdTimestampMixin, SessionIdMixin, TurnIdMixin, TimestampColumnMixin, table=True):
    __tablename__:str = "parent_guide_recommendation_result"

    guides: list[ParentGuideElement] = Field(sa_column=Column(JSON), default=[])

    def to_data_model(self) -> ParentGuideRecommendationResult:
        return ParentGuideRecommendationResult(**self.model_dump())

    @classmethod
    def from_data_model(cls, session_id: str,
                        data_model: ParentGuideRecommendationResult) -> 'ParentGuideRecommendationResultORM':
        return ParentGuideRecommendationResultORM(**data_model.model_dump(), session_id=session_id)


class ParentExampleMessageORM(SQLModel, IdTimestampMixin, SessionIdMixin, table=True):
    __tablename__:str = "parent_example_message"

    recommendation_id: str = Field(foreign_key=f"{ParentGuideRecommendationResultORM.__tablename__}.id")
    guide_id: str = Field(nullable=False, index=True)

    message: str = Field(nullable=False)
    message_localized: Optional[str] = Field(default=None)

    def to_data_model(self) -> ParentExampleMessage:
        return ParentExampleMessage(**self.model_dump())

    @classmethod
    def from_data_model(cls, session_id: str, data_model: ParentExampleMessage) -> 'ParentExampleMessageORM':
        return ParentExampleMessageORM(**data_model.model_dump(), session_id=session_id)


class InteractionORM(SQLModel, IdTimestampMixin, SessionIdMixin, table=True):
    type: InteractionType = Field(nullable=False)
    turn_id: str = Field(nullable=False)
    metadata: dict[str, dict | int | float | str | None] = Field(sa_column=Column(JSON), default=None)