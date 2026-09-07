from datetime import datetime
from uuid import UUID
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime


class ClientCreateResponse(ClientResponse):
    api_key: str


class ManualResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    filename: str
    version: int
    status: str
    error_message: str | None
    uploaded_at: datetime


class SearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: UUID
    manual_id: UUID
    chunk_index: int
    content: str
    section_title: str
    distance: float


class SearchResponse(BaseModel):
    question: str
    results: list[SearchResultItem]


class ErrorResponse(BaseModel):
    detail: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    conversation_id: UUID | None = None
    end_user_identifier: UUID | None = Field(default=None, max_length=255)
    manual_id: UUID | None = None


class SourceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: UUID
    manual_id: UUID
    section_title: str | None
    content: str


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    answer: str
    sources: list[SourceItem]


class MessageItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    created_at: datetime


class ConversationMessagesResponse(BaseModel):
    conversation_id: UUID
    messages: list[MessageItem]


class FeedbackRequest(BaseModel):
    rating: Literal['up', 'down']
    comment: str | None = Field(default=None, max_length=1000)