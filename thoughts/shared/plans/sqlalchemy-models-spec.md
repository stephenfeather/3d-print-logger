# SQLAlchemy ORM Models Specification

**Created**: 2026-01-03
**Purpose**: Define SQLAlchemy models for database abstraction (SQLite/MySQL 8)

## Overview

SQLAlchemy ORM models that work seamlessly with both SQLite (default) and MySQL 8 (production) databases.

### Key Considerations

1. **Type Mapping**: Use SQLAlchemy types that translate correctly to both databases
2. **Auto-increment**: Handle differences in primary key generation
3. **Timestamps**: Automatic created_at/updated_at handling
4. **JSON Support**: Leverage JSON columns for flexible metadata storage
5. **Relationships**: Define ORM relationships for query convenience
6. **Migrations**: Structure for Alembic migration support

---

## Base Configuration

### Database Engine Factory (`src/database/engine.py`)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from src.config import get_config

Base = declarative_base()

def get_database_url() -> str:
    """
    Build database URL from configuration.
    Supports SQLite and MySQL.
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

def create_db_engine():
    """
    Create SQLAlchemy engine with appropriate configuration.
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

# Global engine and session factory
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency for FastAPI routes.
    Provides database session with automatic cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_database():
    """
    Initialize database schema.
    Creates all tables if they don't exist.
    """
    Base.metadata.create_all(bind=engine)
```

---

## Model Definitions

### Mixins for Common Patterns

```python
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declared_attr

class TimestampMixin:
    """
    Adds created_at and updated_at columns.
    Works with both SQLite and MySQL.
    """

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Note: SQLite doesn't support ON UPDATE trigger at DB level,
    # so we rely on SQLAlchemy's onupdate parameter which works at ORM level
```

---

### Model: Printer

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from src.database.engine import Base
from .mixins import TimestampMixin

class Printer(Base, TimestampMixin):
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    location = Column(String(200), nullable=True)
    moonraker_url = Column(String(500), nullable=False)
    moonraker_api_key = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_seen = Column(DateTime, nullable=True)

    # Relationships
    print_jobs = relationship("PrintJob", back_populates="printer", cascade="all, delete-orphan")
    job_totals = relationship("JobTotals", back_populates="printer", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Printer(id={self.id}, name='{self.name}', active={self.is_active})>"
```

**Notes:**
- `String(N)`: Maps to VARCHAR in both databases
- `autoincrement=True`: SQLAlchemy handles AUTO_INCREMENT vs AUTOINCREMENT
- `Boolean`: Maps to TINYINT(1) in MySQL, INTEGER in SQLite
- `cascade="all, delete-orphan"`: Deleting printer removes all related jobs

---

### Model: PrintJob

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy import JSON  # Generic JSON type
from sqlalchemy.orm import relationship
from src.database.engine import Base
from .mixins import TimestampMixin

class PrintJob(Base, TimestampMixin):
    __tablename__ = "print_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    printer_id = Column(Integer, ForeignKey("printers.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String(100), nullable=False)  # Moonraker's UUID
    user = Column(String(100), nullable=True)
    filename = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, index=True)  # completed, error, cancelled, printing, paused

    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    print_duration = Column(Float, nullable=True)  # Seconds
    total_duration = Column(Float, nullable=True)  # Seconds
    filament_used = Column(Float, nullable=True)   # Millimeters

    # JSON columns for flexible metadata
    metadata = Column(JSON, nullable=True)          # Moonraker metadata
    auxiliary_data = Column(JSON, nullable=True)    # Additional tracking

    # Relationships
    printer = relationship("Printer", back_populates="print_jobs")
    job_details = relationship("JobDetails", back_populates="print_job", uselist=False, cascade="all, delete-orphan")

    # Composite unique constraint
    __table_args__ = (
        Index('idx_printer_job', 'printer_id', 'job_id', unique=True),
        Index('idx_printer_status', 'printer_id', 'status'),
    )

    def __repr__(self):
        return f"<PrintJob(id={self.id}, printer_id={self.printer_id}, filename='{self.filename}', status='{self.status}')>"
```

**JSON Column Notes:**
- SQLAlchemy's generic `JSON` type automatically uses:
  - `TEXT` in SQLite (with JSON1 extension for queries)
  - `JSON` native type in MySQL 8
- Both databases support JSON path queries via SQLAlchemy

---

### Model: JobDetails

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.database.engine import Base
from .mixins import TimestampMixin

class JobDetails(Base, TimestampMixin):
    __tablename__ = "job_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    print_job_id = Column(Integer, ForeignKey("print_jobs.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Slicer settings (extracted from gcode)
    layer_height = Column(Float, nullable=True)
    first_layer_height = Column(Float, nullable=True)
    nozzle_temp = Column(Integer, nullable=True)
    bed_temp = Column(Integer, nullable=True)
    print_speed = Column(Integer, nullable=True)
    infill_percentage = Column(Integer, nullable=True)
    infill_pattern = Column(String(50), nullable=True)
    support_enabled = Column(Boolean, nullable=True)
    support_type = Column(String(50), nullable=True)
    filament_type = Column(String(50), nullable=True, index=True)
    filament_brand = Column(String(100), nullable=True)
    filament_color = Column(String(50), nullable=True)

    # Print statistics
    estimated_time = Column(Integer, nullable=True)      # Seconds
    estimated_filament = Column(Float, nullable=True)    # Grams
    layer_count = Column(Integer, nullable=True)
    object_height = Column(Float, nullable=True)         # mm

    # Raw metadata storage
    raw_metadata = Column(JSON, nullable=True)

    # Relationships
    print_job = relationship("PrintJob", back_populates="job_details")

    def __repr__(self):
        return f"<JobDetails(id={self.id}, print_job_id={self.print_job_id}, filament_type='{self.filament_type}')>"
```

**Notes:**
- All slicer fields nullable (not all gcode files have complete metadata)
- `filament_type` indexed for common filtering ("show all PLA prints")
- `raw_metadata` (JSON): Stores complete extracted data for future use

---

### Model: JobTotals

```python
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database.engine import Base

class JobTotals(Base):
    __tablename__ = "job_totals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    printer_id = Column(Integer, ForeignKey("printers.id", ondelete="CASCADE"), nullable=False, unique=True)

    total_jobs = Column(Integer, default=0, nullable=False)
    total_time = Column(Float, default=0.0, nullable=False)        # Seconds (total_duration)
    total_print_time = Column(Float, default=0.0, nullable=False)  # Seconds (print_duration)
    total_filament_used = Column(Float, default=0.0, nullable=False)  # Millimeters
    longest_job = Column(Float, default=0.0, nullable=False)       # Seconds

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    printer = relationship("Printer", back_populates="job_totals")

    def __repr__(self):
        return f"<JobTotals(printer_id={self.printer_id}, total_jobs={self.total_jobs})>"
```

**Update Strategy:**
- Application-level updates after each job completion
- Consider database triggers for MySQL (optional optimization)
- Totals calculated from completed jobs only

---

### Model: ApiKey

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from src.database.engine import Base
from .mixins import TimestampMixin

class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hash
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for display
    name = Column(String(100), nullable=False)       # User-friendly identifier
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ApiKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}', active={self.is_active})>"
```

**Security Notes:**
- Store only SHA-256 hash, never plaintext
- `key_prefix`: For user identification (e.g., "3dp_abc12345")
- `last_used`: Updated on each successful auth
- `expires_at`: Optional expiration (null = never expires)

---

## Helper Functions

### CRUD Operations (`src/database/crud.py`)

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
from .models import Printer, PrintJob, JobDetails, JobTotals, ApiKey

# ========== Printer CRUD ==========

def get_printer(db: Session, printer_id: int) -> Optional[Printer]:
    return db.query(Printer).filter(Printer.id == printer_id).first()

def get_active_printers(db: Session) -> List[Printer]:
    return db.query(Printer).filter(Printer.is_active == True).all()

def create_printer(db: Session, name: str, moonraker_url: str, **kwargs) -> Printer:
    printer = Printer(name=name, moonraker_url=moonraker_url, **kwargs)
    db.add(printer)
    db.commit()
    db.refresh(printer)
    return printer

def update_printer_last_seen(db: Session, printer_id: int):
    """Update last_seen timestamp for health monitoring."""
    db.query(Printer).filter(Printer.id == printer_id).update({
        "last_seen": datetime.utcnow()
    })
    db.commit()

# ========== PrintJob CRUD ==========

def upsert_print_job(db: Session, printer_id: int, job_id: str, **job_data) -> PrintJob:
    """
    Insert or update print job.
    Handles duplicate job_id per printer.
    """
    job = db.query(PrintJob).filter(
        and_(PrintJob.printer_id == printer_id, PrintJob.job_id == job_id)
    ).first()

    if job:
        # Update existing
        for key, value in job_data.items():
            setattr(job, key, value)
    else:
        # Create new
        job = PrintJob(printer_id=printer_id, job_id=job_id, **job_data)
        db.add(job)

    db.commit()
    db.refresh(job)
    return job

def get_jobs_by_printer(db: Session, printer_id: int, status: Optional[str] = None) -> List[PrintJob]:
    query = db.query(PrintJob).filter(PrintJob.printer_id == printer_id)
    if status:
        query = query.filter(PrintJob.status == status)
    return query.order_by(PrintJob.start_time.desc()).all()

# ========== JobTotals Management ==========

def update_job_totals(db: Session, printer_id: int):
    """
    Recalculate totals for a printer.
    Call after job completion.
    """
    # Get or create totals record
    totals = db.query(JobTotals).filter(JobTotals.printer_id == printer_id).first()
    if not totals:
        totals = JobTotals(printer_id=printer_id)
        db.add(totals)

    # Aggregate from completed jobs
    completed_jobs = db.query(PrintJob).filter(
        and_(PrintJob.printer_id == printer_id, PrintJob.status == "completed")
    ).all()

    totals.total_jobs = len(completed_jobs)
    totals.total_time = sum(j.total_duration or 0 for j in completed_jobs)
    totals.total_print_time = sum(j.print_duration or 0 for j in completed_jobs)
    totals.total_filament_used = sum(j.filament_used or 0 for j in completed_jobs)
    totals.longest_job = max((j.total_duration or 0 for j in completed_jobs), default=0)

    db.commit()
    db.refresh(totals)
    return totals

# ========== JobDetails CRUD ==========

def create_job_details(db: Session, print_job_id: int, **details_data) -> JobDetails:
    """Add extracted gcode metadata to job."""
    details = JobDetails(print_job_id=print_job_id, **details_data)
    db.add(details)
    db.commit()
    db.refresh(details)
    return details

# ========== ApiKey Management ==========

def create_api_key(db: Session, key_hash: str, key_prefix: str, name: str, **kwargs) -> ApiKey:
    api_key = ApiKey(key_hash=key_hash, key_prefix=key_prefix, name=name, **kwargs)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key

def get_api_key_by_hash(db: Session, key_hash: str) -> Optional[ApiKey]:
    return db.query(ApiKey).filter(
        and_(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    ).first()

def update_api_key_last_used(db: Session, api_key_id: int):
    db.query(ApiKey).filter(ApiKey.id == api_key_id).update({
        "last_used": datetime.utcnow()
    })
    db.commit()
```

---

## Alembic Migrations

### Setup (`alembic.ini`)

```ini
[alembic]
script_location = src/database/migrations
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname
# (Override via environment variable: DATABASE_URL)

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### Environment Setup (`src/database/migrations/env.py`)

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from src.database.engine import Base, get_database_url
from src.database.models import *  # Import all models

# Alembic Config object
config = context.config

# Set database URL from application config
config.set_main_option("sqlalchemy.url", get_database_url())

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Create Initial Migration

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## Query Examples

### Joining Related Data

```python
from sqlalchemy.orm import joinedload

# Get printer with all jobs and details
printer = db.query(Printer).options(
    joinedload(Printer.print_jobs).joinedload(PrintJob.job_details)
).filter(Printer.id == 1).first()

# Access related data
for job in printer.print_jobs:
    print(f"{job.filename}: {job.status}")
    if job.job_details:
        print(f"  Filament: {job.job_details.filament_type}")
```

### Filtering with JSON Columns

```python
# MySQL: JSON path queries
from sqlalchemy import func

# Find jobs with specific slicer metadata
jobs = db.query(PrintJob).filter(
    func.json_extract(PrintJob.metadata, "$.slicer") == "OrcaSlicer"
).all()

# SQLite: JSON1 extension (similar syntax)
jobs = db.query(PrintJob).filter(
    func.json_extract(PrintJob.metadata, "$.slicer") == "OrcaSlicer"
).all()
```

### Aggregations

```python
from sqlalchemy import func

# Total filament used across all printers
total_filament = db.query(
    func.sum(JobTotals.total_filament_used)
).scalar()

# Jobs per printer
jobs_per_printer = db.query(
    Printer.name,
    func.count(PrintJob.id)
).join(PrintJob).group_by(Printer.id).all()
```

---

## Testing Models

### Pytest Fixtures (`tests/conftest.py`)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.engine import Base
from src.database.models import *

@pytest.fixture
def db_session():
    """
    Create in-memory SQLite database for tests.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()

@pytest.fixture
def sample_printer(db_session):
    """Create sample printer for tests."""
    from src.database.crud import create_printer
    return create_printer(
        db_session,
        name="Test Printer",
        moonraker_url="http://localhost:7125"
    )
```

### Test Example (`tests/test_models.py`)

```python
from datetime import datetime
from src.database.models import Printer, PrintJob
from src.database.crud import create_printer, upsert_print_job

def test_create_printer(db_session):
    printer = create_printer(
        db_session,
        name="Ender 3",
        moonraker_url="http://ender3.local:7125"
    )

    assert printer.id is not None
    assert printer.name == "Ender 3"
    assert printer.is_active is True

def test_upsert_job_creates_new(db_session, sample_printer):
    job = upsert_print_job(
        db_session,
        printer_id=sample_printer.id,
        job_id="abc123",
        filename="test.gcode",
        status="completed",
        start_time=datetime.utcnow()
    )

    assert job.id is not None
    assert job.filename == "test.gcode"

def test_upsert_job_updates_existing(db_session, sample_printer):
    # Create
    job1 = upsert_print_job(
        db_session,
        printer_id=sample_printer.id,
        job_id="abc123",
        filename="test.gcode",
        status="printing",
        start_time=datetime.utcnow()
    )

    # Update
    job2 = upsert_print_job(
        db_session,
        printer_id=sample_printer.id,
        job_id="abc123",
        status="completed",
        end_time=datetime.utcnow()
    )

    assert job1.id == job2.id  # Same record
    assert job2.status == "completed"
```

---

## Dependencies

### Python Requirements

```txt
# requirements.txt
sqlalchemy>=2.0.0
pymysql>=1.0.0        # MySQL driver
alembic>=1.12.0       # Migrations
```

---

## Next Steps

1. **Implement models** in `src/database/models.py`
2. **Create initial migration** with Alembic
3. **Test against both databases** (SQLite and MySQL)
4. **Build CRUD operations** in `src/database/crud.py`
5. **Integrate with FastAPI** routes

---

## References

- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [MySQL vs SQLite Compatibility](https://docs.sqlalchemy.org/en/20/dialects/)
