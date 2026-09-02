from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import ManualChunk
from app.services.embeddings import embed_query

TOP_K = 5
MAX_DISTANCE = 0.6
EF_SEARCH = 100


@dataclass
class RetrievedChunk:
    chunk_id: UUID
    manual_id: UUID
    chunk_index: int
    content: str
    section_title: str | None
    distance: float


def retrieve(
    db: Session,
    client_id: UUID,
    question: str,
    top_k: int = TOP_K,
    max_distance: float = MAX_DISTANCE,
    manual_id: UUID | None = None,
) -> list[RetrievedChunk]:
    """Return the chunks most similar to the question for one client"""
    vector = embed_query(question)

    db.execute(text(f'SET LOCAL hnsw.ef_search = {EF_SEARCH}'))

    distance = ManualChunk.embedding.cosine_distance(vector)

    stmt = (
        select(ManualChunk, distance.label('distance'))
        .where(ManualChunk.client_id == client_id)
        .where(ManualChunk.embedding.is_not(None))
        .order_by(distance)
        .limit(top_k)
    )

    if manual_id is not None:
        stmt = stmt.where(ManualChunk.manual_id == manual_id)

    rows = db.execute(stmt).all()

    return [
        RetrievedChunk(
            chunk_id=chunk.id,
            manual_id=chunk.manual_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            section_title=chunk.section_title,
            distance=float(dist)
        )
        for chunk, dist in rows
        if dist <= max_distance
    ]

