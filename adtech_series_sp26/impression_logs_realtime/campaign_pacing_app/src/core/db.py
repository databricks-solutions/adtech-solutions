"""
Database engine with OAuth token injection for Lakebase Provisioned.

Tokens expire after ~1 hour. Using pool_recycle=3300 (55 min) ensures connections
are recycled before expiry, triggering a fresh token via the do_connect listener.
"""
import uuid
from typing import Generator

from databricks.sdk import WorkspaceClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

_client = WorkspaceClient()


def _get_pg_host() -> str:
    """Return Lakebase host — env var if injected by Apps, else SDK lookup."""
    if settings.PGHOST:
        return settings.PGHOST
    instance = _client.database.get_database_instance(name=settings.LAKEBASE_INSTANCE)
    return instance.read_write_dns


def _generate_token() -> str:
    cred = _client.database.generate_database_credential(
        request_id=str(uuid.uuid4()),
        instance_names=[settings.LAKEBASE_INSTANCE],
    )
    return cred.token


def _create_engine():
    pg_host = _get_pg_host()
    username = _client.current_user.me().user_name

    # username in URL (no password — injected via do_connect)
    url = f"postgresql+psycopg://{username}@{pg_host}:5432/{settings.PGDATABASE}?sslmode=require"

    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=3300,  # recycle connections before the 1-hour token expiry
    )

    @event.listens_for(engine, "do_connect")
    def inject_token(dialect, conn_rec, cargs, cparams):
        cparams["password"] = _generate_token()

    return engine


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
