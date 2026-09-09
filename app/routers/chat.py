from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_client
from app.models import (
    AnswerComparison,
    Client,
    Conversation,
    Message,
    MessageSource,
)
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationMessagesResponse,
    FeedbackRequest,
    MessageItem,
    SourceItem,
)
from app.services.generation import Generation, GenerationError, generate_answer
from app.services.retrieval import RetrievedChunk, retrieve
from app.services.tracing import record_feedback, trace_chat

router = APIRouter(prefix='/chat', tags=['chat'])

NO_ANSWER = (
    'I could not find this in the manual.'
    'Please contact support for help with this question.'
)


@router.post('', response_model=ChatResponse)
def create_chat_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_client: Client = Depends(get_current_client),
) -> ChatResponse:
    conversation = _get_or_create_conversation(db, current_client, payload)

    with trace_chat(
        question=payload.question,
        client_id=current_client.id,
        conversation_id=conversation.id,
    ) as trace:

        db.add(Message(
            conversation_id=conversation.id,
            role='user',
            content=payload.question,
        ))
        db.flush()

        with trace.span('retrieval') as span:
            chunks = retrieve(
                db=db,
                client_id=current_client.id,
                question=payload.question,
                manual_id=payload.manual_id,
            )
            span.update(output={
                'count': len(chunks),
                'distances': [round(c.distance, 4) for c in chunks],
                'sections': [c.section_title for c in chunks],
            })

        if not chunks:
            trace.output(NO_ANSWER, refused=True)

            message = Message(
                conversation_id=conversation.id,
                role='assistant',
                content=NO_ANSWER,
                trace_id=trace.id,
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            return ChatResponse(
                conversation_id=conversation.id,
                message_id=message.id,
                answer=NO_ANSWER,
                sources=[],
            )

        try:
            result = generate_answer(payload.question, chunks, settings.chat_model)
        except GenerationError as e:
            trace.error(str(e))
            db.commit()
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e

        trace.output(result.answer)

        message = Message(
            conversation_id=conversation.id,
            role='assistant',
            content=result.answer,
            trace_id=trace.id,
            model=result.model,
        )
        db.add(message)
        db.flush()

        db.add_all([
            MessageSource(
                message_id=message.id,
                chunk_id=chunk.chunk_id,
                distance=chunk.distance,
                rank=i,
            )
            for i, chunk in enumerate(chunks, start=1)
        ])

        if settings.comparison_enabled:
            _record_comparison(
                db, trace, message, payload.question, chunks, result
            )
        db.commit()
        db.refresh(message)

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=message.id,
        answer=result.answer,
        sources=[
            SourceItem(
                chunk_id=chunk.chunk_id,
                manual_id=chunk.manual_id,
                section_title=chunk.section_title,
                content=chunk.content,
            )
            for chunk in chunks
        ],
    )


@router.get('/{conversation_id}/messages', response_model=ConversationMessagesResponse)
def get_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_client: Client = Depends(get_current_client),
) -> ConversationMessagesResponse:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.client_id == current_client.id,
        )
    )

    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Conversation not found.')

    messages = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).all()

    return ConversationMessagesResponse(
        conversation_id=conversation.id,
        messages=[MessageItem.model_validate(m) for m in messages],
    )


@router.post('/messages/{message_id}/feedback', status_code=status.HTTP_204_NO_CONTENT)
def submit_feedback(
    message_id: UUID,
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    current_client: Client = Depends(get_current_client),
) -> None:
    message = db.scalar(
        select(Message)
        .join(Conversation)
        .where(
            Message.id == message_id,
            Conversation.client_id == current_client.id,
        )
    )
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Message not found.')
    if message.trace_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Feedback can only be submitted for assistant answers.',
        )

    record_feedback(message.trace_id, payload.rating, payload.comment)


def _record_comparison(
    db: Session,
    trace,
    message: Message,
    question: str,
    chunks: list[RetrievedChunk],
    result_a: Generation,
) -> None:
    """Now run the second model on the same chunks and store both answers for comparison"""
    try:
        with trace.span('comparison'):
            result_b = generate_answer(question, chunks, settings.chat_model_b)
    except GenerationError as e:
        print(f'Comparison failed for message {message.id}: {e}')
        return

    db.add(AnswerComparison(
        message_id=message.id,
        question=question,
        chunk_ids=[chunk.chunk_id for chunk in chunks],
        best_distance=chunks[0].distance,
        model_a=result_a.model,
        answer_a=result_a.answer,
        prompt_tokens_a=result_a.prompt_tokens,
        completion_tokens_a=result_a.completion_tokens,
        cost_a=result_a.cost,
        latency_ms_a=result_a.latency_ms,
        model_b=result_b.model,
        answer_b=result_b.answer,
        prompt_tokens_b=result_b.prompt_tokens,
        completion_tokens_b=result_b.completion_tokens,
        cost_b=result_b.cost,
        latency_ms_b=result_b.latency_ms,
        trace_id=trace.id,
    ))


def _get_or_create_conversation(
    db: Session,
    client: Client,
    payload: ChatRequest,
) -> Conversation:
    if payload.conversation_id is not None:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.id == payload.conversation_id,
                Conversation.client_id == client.id,
            )
        )
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Conversation not found.',
            )
        return conversation

    conversation = Conversation(
        client_id=client.id,
        end_user_identifier=payload.end_user_identifier,
    )
    db.add(conversation)
    db.flush()
    return conversation