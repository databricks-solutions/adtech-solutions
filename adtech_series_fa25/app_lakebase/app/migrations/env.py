from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from databricks.sdk import WorkspaceClient
from utils.lakebase import get_engine
from models import Base

# Assign our metadata targets from our models.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    database_instance_name = config.get_section_option("databricks", "instance_name")
    database_name = config.get_section_option("databricks", "database_name")
    profile_name = config.get_section_option("databricks", "profile_name")
    databricks_client = None

    assert database_instance_name is not None, "database_instance_name is required"
    assert database_name is not None, "database_name is required"

    if profile_name is not None:
        databricks_client = WorkspaceClient(profile=profile_name)
    else:
        databricks_client = WorkspaceClient()

    connectable = get_engine(databricks_client, database_instance_name, database_name)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
