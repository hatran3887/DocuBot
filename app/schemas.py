from datetime import datetime
from uuid import UUID

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