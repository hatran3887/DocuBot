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


class ErrorResponse(BaseModel):
    detail: str