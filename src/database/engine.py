"""
Database engine setup for 3D Print Logger.

Provides database engine factory supporting both SQLite and MySQL,
session management, and database initialization utilities.
"""

from typing import Generator
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.pool import StaticPool

from src.config import get_config

class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass


def get_database_url() -> str:
    """
    Build database URL from configuration.
    Supports SQLite and MySQL.

    Returns:
        str: SQLAlchemy database URL.

    Raises:
        ValueError: If database type is not supported.
    """
    config = get_config()
    db_type = config.database.type

    if db_type == "sqlite":
        db_path = config.database.path
        return f"sqlite:///{db_path}"

    elif db_type == "mysql":
        user = config.database.user
        password = config.database.password
        host = config.database.host
        port = config.database.port
        database = config.database.database
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def create_db_engine() -> Engine:
    """
    Create SQLAlchemy engine with appropriate configuration.

    Returns:
        Engine: SQLAlchemy engine configured for the database type.
    """
    url = get_database_url()
    config = get_config()

    if config.database.type == "sqlite":
        # SQLite-specific options
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},  # Allow multi-threaded access
            poolclass=StaticPool,  # Single connection pool for SQLite
            echo=config.logging.level == "DEBUG"
        )
    else:
        # MySQL-specific options
        engine = create_engine(
            url,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=config.logging.level == "DEBUG"
        )

    return engine


def create_session_factory(engine: Engine) -> sessionmaker:
    """
    Create a session factory bound to the given engine.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        sessionmaker: Session factory.
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Global engine and session factory (lazy initialization)
_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    """Get or create the global database engine."""
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def get_session_local() -> sessionmaker:
    """Get or create the global session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = create_session_factory(get_engine())
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes.
    Provides database session with automatic cleanup.

    Yields:
        Session: Database session.
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    """
    Initialize database schema.
    Creates all tables if they don't exist.
    """
    # Import models to ensure they're registered with Base
    from src.database import models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(bind=engine)


async def async_init_database() -> None:
    """
    Async wrapper for database initialization.
    For use with FastAPI startup events.
    """
    init_database()


def reset_engine() -> None:
    """Reset the global engine and session factory. Useful for testing."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
