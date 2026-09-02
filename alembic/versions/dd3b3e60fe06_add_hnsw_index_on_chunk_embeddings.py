"""add hnsw index on chunk embeddings

Revision ID: dd3b3e60fe06
Revises: 0c04db5809d0
Create Date: 2026-09-02 11:49:01.487381

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd3b3e60fe06'
down_revision: Union[str, Sequence[str], None] = '0c04db5809d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX ix_manual_chunks_embedding "
        "ON manual_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_manual_chunks_embedding")
