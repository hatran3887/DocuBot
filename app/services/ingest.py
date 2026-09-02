from uuid import UUID

from app.database import SessionLocal
from app.models import Manual, ManualChunk
from app.services.chunking import chunk_text
from app.services.extraction import ExtractionError, load_text

MARKDOWN_SUFFIXES = {'.md', '.markdown'}


def process_manual(manual_id: UUID) -> None:
    db = SessionLocal()
    try:
        manual = db.get(Manual, manual_id)
        if manual is None:
            return

        manual.status = 'processing'
        db.commit()

        path = manual.storage_path
        text = load_text(path)
        chunks = chunk_text(text, path.suffix.lower() in MARKDOWN_SUFFIXES)

        if not chunks:
            raise ExtractionError('File produced no chunks.')

        db.add_all([
            ManualChunk(
                manual_id=manual.id,
                client_id=manual.client_id,
                chunk_index=chunk.index,
                content=chunk.content,
                page_number=None,
                section_title=chunk.section_title,
                token_count=chunk.token_count,
            )
            for chunk in chunks
        ])

        manual.status = 'ready'
        manual.error_message = None
        db.commit()

    except ExtractionError as e:
        _mark_failed(db, manual_id, str(e))
    except Exception as e:
        _mark_failed(db, manual_id, f'Unexpected error: {e}')
        raise
    finally:
        db.close()


def _mark_failed(db, manual_id: UUID, message: str) -> None:
    db.rollback()
    manual = db.get(Manual, manual_id)
    if manual is not None:
        manual.status = 'failed'
        manual.error_message = message[:500]
        db.commit()