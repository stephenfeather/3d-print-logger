"""
Alembic migration environment configuration.

This module configures Alembic to use our SQLAlchemy models and database settings.
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, event

from alembic import context

# Import our models and base
from src.database.engine import Base
from src.database.models import (  # noqa: F401 - imports needed for autogenerate
    Printer,
    PrintJob,
    JobDetails,
    JobTotals,
    ApiKey,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def get_database_url() -> str:
    """
    Get database URL from environment or config.

    Priority:
    1. DATABASE_URL environment variable
    2. Build from individual components (DATABASE_TYPE, etc.)
    3. Default SQLite path
    """
    # Check for direct DATABASE_URL
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    # Build from components
    db_type = os.environ.get("DATABASE_TYPE", "sqlite")

    if db_type == "sqlite":
        db_path = os.environ.get("DATABASE_PATH", "./data/printlog.db")
        return f"sqlite:///{db_path}"
    elif db_type == "mysql":
        user = os.environ.get("DATABASE_USER", "printlog")
        password = os.environ.get("DATABASE_PASSWORD", "")
        host = os.environ.get("DATABASE_HOST", "localhost")
        port = os.environ.get("DATABASE_PORT", "3306")
        database = os.environ.get("DATABASE_NAME", "printlog")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


# Override the sqlalchemy.url from alembic.ini with our dynamic URL
config.set_main_option("sqlalchemy.url", get_database_url())

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter objects to include in migrations.

    This can be used to exclude certain tables or columns from migrations.
    """
    # Include all objects by default
    return True


def _set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys for SQLite connections."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


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
        include_object=include_object,
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Enable foreign keys for SQLite
    url = config.get_main_option("sqlalchemy.url")
    if url and url.startswith("sqlite"):
        event.listen(connectable, "connect", _set_sqlite_pragma)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            render_as_batch=True,  # Required for SQLite ALTER TABLE support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
