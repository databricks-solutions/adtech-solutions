"""empty message

Revision ID: 3032b3b6ae29
Revises: 9bec402eac59
Create Date: 2025-08-15 10:54:11.795764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3032b3b6ae29'
down_revision: Union[str, None] = '9bec402eac59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE INDEX IF NOT EXISTS message_embeddings_embedding_cos_idx
    ON message_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);
    """)


def downgrade() -> None:
    op.execute("""
    DROP INDEX IF EXISTS message_embeddings_embedding_cos_idx;
    """)
