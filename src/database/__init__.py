"""
Database package for 3D Print Logger.

Contains SQLAlchemy ORM models, database engine setup, and migrations.
"""

from src.database.engine import (
    Base,
    get_database_url,
    create_db_engine,
    create_session_factory,
    get_engine,
    get_session_local,
    get_db,
    init_database,
    async_init_database,
    reset_engine,
)

from src.database.models import (
    TimestampMixin,
    Printer,
    PrintJob,
    JobDetails,
    JobTotals,
    ApiKey,
)

from src.database.crud import (
    # Printer CRUD
    get_printer,
    get_active_printers,
    create_printer,
    update_printer_last_seen,
    # PrintJob CRUD
    upsert_print_job,
    get_jobs_by_printer,
    # JobTotals CRUD
    update_job_totals,
    # JobDetails CRUD
    create_job_details,
    # ApiKey CRUD
    create_api_key,
    get_api_key_by_hash,
    update_api_key_last_used,
)

__all__ = [
    # Engine
    "Base",
    "get_database_url",
    "create_db_engine",
    "create_session_factory",
    "get_engine",
    "get_session_local",
    "get_db",
    "init_database",
    "async_init_database",
    "reset_engine",
    # Models
    "TimestampMixin",
    "Printer",
    "PrintJob",
    "JobDetails",
    "JobTotals",
    "ApiKey",
    # CRUD Operations
    "get_printer",
    "get_active_printers",
    "create_printer",
    "update_printer_last_seen",
    "upsert_print_job",
    "get_jobs_by_printer",
    "update_job_totals",
    "create_job_details",
    "create_api_key",
    "get_api_key_by_hash",
    "update_api_key_last_used",
]
