"""Adding Databricks access role

Revision ID: fef90431bf2c
Revises: 
Create Date: 2025-07-24 15:39:30.675624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fef90431bf2c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS databricks_auth;")
    op.execute("SELECT databricks_create_role('Adtech Series DB Access Role','GROUP');")
    op.execute('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "Adtech Series DB Access Role";')
    op.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "Adtech Series DB Access Role";')
    op.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "Adtech Series DB Access Role";')
    pass


def downgrade() -> None:
    op.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE USAGE, SELECT ON ALL SEQUENCES FROM "Adtech Series DB Access Role";')
    op.execute('REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM "Adtech Series DB Access Role";')
    op.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM "Adtech Series DB Access Role";')
    op.execute('DROP ROLE IF EXISTS "Adtech Series DB Access Role";')
    op.execute("DROP EXTENSION IF EXISTS databricks_auth;")   
    pass
