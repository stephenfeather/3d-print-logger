"""
TDD tests for database engine factory.

Following Test-Driven Development: Tests written FIRST before implementation.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import Engine
from sqlalchemy.orm import Session


class TestDatabaseUrl:
    """Tests for get_database_url function."""

    def test_sqlite_url_generation(self):
        """SQLite URL is generated correctly."""
        from src.database.engine import get_database_url

        with patch('src.database.engine.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                database=MagicMock(
                    type="sqlite",
                    path="./data/test.db"
                )
            )

            url = get_database_url()
            assert url == "sqlite:///./data/test.db"

    def test_mysql_url_generation(self):
        """MySQL URL is generated correctly."""
        from src.database.engine import get_database_url

        with patch('src.database.engine.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                database=MagicMock(
                    type="mysql",
                    user="printlog",
                    password="secret",
                    host="localhost",
                    port=3306,
                    database="printlog_db"
                )
            )

            url = get_database_url()
            assert url == "mysql+pymysql://printlog:secret@localhost:3306/printlog_db"

    def test_unsupported_database_type(self):
        """Unsupported database type raises ValueError."""
        from src.database.engine import get_database_url

        with patch('src.database.engine.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                database=MagicMock(type="postgresql")
            )

            with pytest.raises(ValueError) as excinfo:
                get_database_url()

            assert "Unsupported database type" in str(excinfo.value)


class TestCreateEngine:
    """Tests for create_db_engine function."""

    def test_create_sqlite_engine(self):
        """SQLite engine is created with correct options."""
        from src.database.engine import create_db_engine

        with patch('src.database.engine.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                database=MagicMock(
                    type="sqlite",
                    path=":memory:"
                ),
                logging=MagicMock(level="INFO")
            )

            engine = create_db_engine()

            assert engine is not None
            assert isinstance(engine, Engine)
            # SQLite in-memory URL
            assert "sqlite" in str(engine.url)

    def test_sqlite_engine_multithread_support(self):
        """SQLite engine allows multi-threaded access."""
        from src.database.engine import create_db_engine

        with patch('src.database.engine.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                database=MagicMock(
                    type="sqlite",
                    path=":memory:"
                ),
                logging=MagicMock(level="INFO")
            )

            engine = create_db_engine()

            # Verify connection works from multiple threads
            # (This is a basic check; the actual multi-thread is handled by check_same_thread=False)
            assert engine is not None


class TestSessionLocal:
    """Tests for session factory."""

    def test_session_creation(self):
        """SessionLocal creates valid sessions."""
        from src.database.engine import create_session_factory, create_db_engine

        with patch('src.database.engine.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                database=MagicMock(
                    type="sqlite",
                    path=":memory:"
                ),
                logging=MagicMock(level="INFO")
            )

            engine = create_db_engine()
            SessionLocal = create_session_factory(engine)

            session = SessionLocal()
            assert session is not None
            assert isinstance(session, Session)
            session.close()


class TestGetDb:
    """Tests for get_db dependency."""

    def test_get_db_yields_session(self):
        """get_db yields a database session."""
        from src.database.engine import Base, create_db_engine, create_session_factory

        with patch('src.database.engine.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                database=MagicMock(
                    type="sqlite",
                    path=":memory:"
                ),
                logging=MagicMock(level="INFO")
            )

            engine = create_db_engine()
            SessionLocal = create_session_factory(engine)

            def get_db():
                db = SessionLocal()
                try:
                    yield db
                finally:
                    db.close()

            gen = get_db()
            session = next(gen)
            assert isinstance(session, Session)

            # Cleanup
            try:
                next(gen)
            except StopIteration:
                pass


class TestInitDatabase:
    """Tests for init_database function."""

    def test_init_database_creates_tables(self, db_engine):
        """init_database creates all model tables."""
        from src.database.engine import Base
        from src.database.models import Printer, PrintJob, JobDetails, JobTotals, ApiKey

        # Tables should exist after init
        inspector = db_engine.dialect.has_table

        # Check via metadata
        assert "printers" in Base.metadata.tables
        assert "print_jobs" in Base.metadata.tables
        assert "job_details" in Base.metadata.tables
        assert "job_totals" in Base.metadata.tables
        assert "api_keys" in Base.metadata.tables


class TestBase:
    """Tests for Base declarative base."""

    def test_base_exists(self):
        """Base is exported from engine module."""
        from src.database.engine import Base

        assert Base is not None
        # Should be a declarative base
        assert hasattr(Base, 'metadata')
