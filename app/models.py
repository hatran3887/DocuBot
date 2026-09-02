from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
from pathlib import Path

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Float,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.database import Base


class Client(Base):
    __tablename__ = 'clients'

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    api_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    manuals: Mapped[list['Manual']] = relationship(
        back_populates='client', cascade='all, delete-orphan'
    )
    conversations: Mapped[list['Conversation']] = relationship(
        back_populates='client', cascade='all, delete-orphan'
    )


class Manual(Base):
    __tablename__ = 'manuals'

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    client_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey('clients.id', ondelete='CASCADE'),
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default='uploaded')
    error_message: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    client: Mapped['Client'] = relationship(back_populates='manuals')
    chunks: Mapped[list['ManualChunk']] = relationship(
        back_populates='manual', cascade='all, delete-orphan'
    )

    @property
    def storage_path(self) -> Path:
        return settings.upload_dir / self.stored_filename


class ManualChunk(Base):
    __tablename__ = 'manual_chunks'

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    manual_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey('manuals.id', ondelete='CASCADE'),
        index=True,
    )
    client_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey('clients.id', ondelete='CASCADE'),
        index=True,
    )
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    chunk_index: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int | None]
    section_title: Mapped[str | None] = mapped_column(String(255))
    token_count: Mapped[int] = mapped_column(Integer)
    section_reference: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("manual_id", "chunk_index", name="uq_chunk_per_manual"),
    )

    manual: Mapped['Manual'] = relationship(back_populates='chunks')


class Conversation(Base):
    __tablename__ = 'conversations'

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    client_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey('clients.id', ondelete='CASCADE'),
        index=True,
    )
    end_user_identifier: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    client: Mapped['Client'] = relationship(back_populates='conversations')
    messages: Mapped[list['Message']] = relationship(
        back_populates='conversation', cascade='all, delete-orphan'
    )


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    conversation_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey('conversations.id', ondelete='CASCADE'),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    conversation: Mapped['Conversation'] = relationship(back_populates='messages')
    sources: Mapped[list['MessageSource']] = relationship(
        back_populates='message', cascade='all, delete-orphan'
    )
    generation_log: Mapped['GenerationLog | None'] = relationship(
        back_populates='message', cascade='all, delete-orphan', uselist=False
    )


class MessageSource(Base):
    __tablename__ = 'message_sources'

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    message_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey('messages.id', ondelete='CASCADE'),
        index=True,
    )
    chunk_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey('manual_chunks.id', ondelete='CASCADE'),
    )
    relevance_score: Mapped[float | None] = mapped_column(Float)
    message: Mapped['Message'] = relationship(back_populates='sources')


class GenerationLog(Base):
    __tablename__ = 'generation_logs'

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    message_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey('messages.id', ondelete='CASCADE'),
    )
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    prompt_technique: Mapped[str | None] = mapped_column(String(100))
    temperature: Mapped[float | None] = mapped_column(Float)
    max_tokens: Mapped[int | None] = mapped_column(Integer)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_estimate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    message: Mapped['Message | None'] = relationship(back_populates='generation_log')
