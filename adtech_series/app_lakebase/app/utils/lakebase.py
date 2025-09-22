from databricks.sdk import WorkspaceClient
import uuid
import os
import sys
import logging
import time
from typing import Optional
from sqlalchemy import create_engine, event
import threading

# Token refresh tracking
_token_cache = {}
_token_lock = threading.Lock()

def _get_fresh_credentials(client: WorkspaceClient, db_name: str):
    """Generate fresh database credentials with timestamp tracking."""
    with _token_lock:
        cache_key = f"{db_name}_{id(client)}"
        current_time = time.time()

        # Check if we have cached credentials that are still valid (55 minutes = 3300 seconds)
        if cache_key in _token_cache:
            cached_data = _token_cache[cache_key]
            if current_time - cached_data['timestamp'] < 3300:  # 55 minutes
                return cached_data['credentials'], cached_data['database']

        # Generate new credentials
        database = client.database.get_database_instance(db_name)
        credentials = client.database.generate_database_credential(
            instance_names=[db_name],
            request_id=str(uuid.uuid4())
        )

        # Cache the new credentials
        _token_cache[cache_key] = {
            'credentials': credentials,
            'database': database,
            'timestamp': current_time
        }

        return credentials, database

def get_postgres_connection(
    client: WorkspaceClient,
    db_name: str,
    database_name: Optional[str] = "databricks_postgres"
) -> str:
    """
    Get PostgreSQL connection string using Databricks SDK.

    Args:
        client (WorkspaceClient): The Databricks workspace client.
        db_name (str): The name of the database instance.
        database_name (Optional[str], optional): The name of the database to connect to.
            Defaults to "databricks_postgres".

    Returns:
        str: SQLAlchemy-compatible PostgreSQL connection string.
    """
    credentials, database = _get_fresh_credentials(client, db_name)

    # Use POSTGRES_GROUP env var as username if set, otherwise use current user
    postgres_group = os.getenv('POSTGRES_GROUP')
    username = postgres_group if postgres_group else client.current_user.me().user_name

    database_info = {
        "host": database.read_write_dns,
        "port": "5432",
        "database": database_name,
        "username": username,
        "password": credentials.token,
        "ssl_mode": "require"
    }

    database_url = (
        f"postgresql://{database_info['username']}:{database_info['password']}"
        f"@{database_info['host']}:{database_info['port']}/"
        f"{database_info['database']}?sslmode={database_info['ssl_mode']}"
    )

    return database_url

def get_jdbc_url(
    client: WorkspaceClient,
    db_name: str,
    database_name: Optional[str] = "databricks_postgres"
) -> str:
    """
    Get JDBC URL for PostgreSQL connection using Databricks SDK.

    Args:
        client (WorkspaceClient): The Databricks workspace client.
        db_name (str): The name of the database instance.
        database_name (Optional[str], optional): The name of the database to connect to.
            Defaults to "databricks_postgres".

    Returns:
        str: JDBC-compatible PostgreSQL connection string.
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Attempting to get database instance: {db_name}")
    print(f"DEBUG: Attempting to get database instance: {db_name}", file=sys.stderr)

    credentials, database = _get_fresh_credentials(client, db_name)

    # Use POSTGRES_GROUP env var as username if set, otherwise use current user
    postgres_group = os.getenv('POSTGRES_GROUP')
    username = postgres_group if postgres_group else client.current_user.me().user_name

    database_info = {
        "host": database.read_write_dns,
        "port": "5432",
        "database": database_name,
        "username": username,
        "password": credentials.token,
        "ssl_mode": "require"
    }

    jdbc_url = (
        f"jdbc:postgresql://{database_info['host']}:{database_info['port']}/"
        f"{database_info['database']}?sslmode={database_info['ssl_mode']}"
        f"&user={database_info['username']}&password={database_info['password']}"
    )

    return jdbc_url

def get_engine(client: WorkspaceClient, db_name: str, database_name: Optional[str] = "databricks_postgres"):
    """
    Gets a SQLAlchemy engine for the specified Lakebase database with automatic token refresh.

    This function retrieves the connection URL for the given database from Lakebase and returns a SQLAlchemy engine instance
    with automatic OAuth token refresh using SQLAlchemy events.

    Args:
        client (WorkspaceClient): The Databricks workspace client.
        db_name (str): The name of the database in Lakebase.
        database_name (Optional[str], default="databricks_postgres"): The Lakebase database connection profile to use.

    Returns:
        sqlalchemy.engine.Engine: A SQLAlchemy engine connected to the specified Lakebase database.
    """
    # Get initial credentials for the connection URL
    initial_credentials, initial_database = _get_fresh_credentials(client, db_name)

    # Use POSTGRES_GROUP env var as username if set, otherwise use current user
    postgres_group = os.getenv('POSTGRES_GROUP')
    username = postgres_group if postgres_group else client.current_user.me().user_name

    # Create initial connection URL (password will be refreshed via events)
    database_url = (
        f"postgresql://{username}:{initial_credentials.token}"
        f"@{initial_database.read_write_dns}:5432/"
        f"{database_name}?sslmode=require"
    )

    engine = create_engine(database_url, pool_pre_ping=True)

    # Add event listener for automatic token refresh
    @event.listens_for(engine, "do_connect")
    def _refresh_token_on_connect(dialect, conn_rec, cargs, cparams):
        """Refresh OAuth token before establishing new connections."""
        try:
            fresh_credentials, fresh_database = _get_fresh_credentials(client, db_name)
            # Update connection parameters with fresh token
            cparams['password'] = fresh_credentials.token

            logger = logging.getLogger(__name__)
            logger.debug(f"Refreshed OAuth token for database connection: {db_name}")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to refresh OAuth token: {e}")
            raise

    return engine