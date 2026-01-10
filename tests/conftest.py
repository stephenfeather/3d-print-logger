"""
Pytest configuration and fixtures for 3D Print Logger tests.

Provides shared fixtures for database sessions, test clients,
mock printers, and other test utilities.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import models once at module level to avoid re-registration issues
from src.database.engine import Base
from src.database.models import Printer, PrintJob, JobDetails, JobTotals, ApiKey, MaintenanceRecord


def _set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="function")
def db_engine():
    """Create an in-memory SQLite engine for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # Enable foreign key constraints for SQLite
    event.listen(engine, "connect", _set_sqlite_pragma)

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide a test database session."""
    Session = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = Session()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def sample_printer(db_session):
    """Create a sample printer for tests."""
    from src.database.models import Printer

    printer = Printer(
        name="Test Printer",
        moonraker_url="http://localhost:7125",
        location="Test Lab",
        is_active=True
    )
    db_session.add(printer)
    db_session.commit()
    db_session.refresh(printer)

    return printer


@pytest.fixture
def sample_print_job(db_session, sample_printer):
    """Create a sample print job for tests."""
    from src.database.models import PrintJob

    job = PrintJob(
        printer_id=sample_printer.id,
        job_id="sample-job-123",
        filename="sample_print.gcode",
        status="completed",
        start_time=datetime.utcnow(),
        print_duration=3600.0,
        filament_used=10000.0
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    return job


@pytest.fixture
def client(db_session):
    """Provide a FastAPI test client with database session override."""
    from fastapi.testclient import TestClient

    from src.database.engine import get_db
    from src.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def test_api_key(db_session) -> str:
    """Create a test API key and return the full key."""
    from src.api.auth import hash_api_key
    from src.database.crud import create_api_key

    full_key = "3dp_test1234567890abcdef1234567890abcdef1234567890abcdef1234"
    key_hash = hash_api_key(full_key)
    key_prefix = full_key[:12]

    create_api_key(
        db_session,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name="Test API Key",
    )

    return full_key


@pytest.fixture
def auth_headers(test_api_key) -> dict:
    """Return headers with valid API key."""
    return {"X-API-Key": test_api_key}


@pytest.fixture
def sample_job(db_session, sample_printer):
    """Create a sample print job for API tests."""
    from src.database.models import PrintJob

    job = PrintJob(
        printer_id=sample_printer.id,
        job_id="test-job-123",
        filename="test_print.gcode",
        status="completed",
        start_time=datetime.now(timezone.utc),
        print_duration=3600.0,
        filament_used=10000.0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    return job
