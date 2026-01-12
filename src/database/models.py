"""
SQLAlchemy ORM models for 3D Print Logger.

Defines the database schema for printers, print jobs, job details,
job totals, and API keys. Supports both SQLite and MySQL 8.
"""

from datetime import datetime, UTC
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    TypeDecorator,
)
from sqlalchemy.orm import relationship

from src.database.engine import Base


class UTCDateTime(TypeDecorator):
    """
    A DateTime type that stores times in UTC and retrieves them as timezone-aware UTC datetimes.

    Works with SQLite and other databases that don't have native timezone support.
    All datetimes are stored in UTC and assumed to be UTC when retrieved.
    """
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert timezone-aware datetime to naive UTC for storage."""
        if value is None:
            return None
        if value.tzinfo is not None:
            # Convert to UTC if not already
            value = value.astimezone(UTC)
        # Return as naive datetime (SQLite doesn't support timezone)
        return value.replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        """Convert stored naive datetime back to timezone-aware UTC."""
        if value is None:
            return None
        # Assume the stored datetime is in UTC and make it timezone-aware
        return value.replace(tzinfo=UTC)


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at columns.
    Works with both SQLite and MySQL.
    """

    created_at = Column(
        UTCDateTime(),
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    updated_at = Column(
        UTCDateTime(),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )


class Printer(Base, TimestampMixin):
    """
    Printer model.

    Tracks each printer instance and its Moonraker connection details.
    """

    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    location = Column(String(200), nullable=True)
    moonraker_url = Column(String(500), nullable=False)
    moonraker_api_key = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_seen = Column(UTCDateTime(), nullable=True)

    # Printer hardware details (Issue #8)
    printer_type = Column(String(50), nullable=True)  # FDM, Resin, SLS
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    description = Column(String(500), nullable=True)

    # Printer specifications
    filament_diameter = Column(Float, nullable=True, default=1.75)  # 1.75, 2.85, 3.0
    nozzle_diameter = Column(Float, nullable=True)
    bed_x = Column(Float, nullable=True)  # mm
    bed_y = Column(Float, nullable=True)  # mm
    bed_z = Column(Float, nullable=True)  # mm
    has_heated_bed = Column(Boolean, default=False, nullable=False)
    has_heated_chamber = Column(Boolean, default=False, nullable=False)

    # Material tracking (Spoolman integration future)
    loaded_materials = Column(JSON, nullable=True)

    # Relationships
    print_jobs = relationship(
        "PrintJob",
        back_populates="printer",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    job_totals = relationship(
        "JobTotals",
        back_populates="printer",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    maintenance_records = relationship(
        "MaintenanceRecord",
        back_populates="printer",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Printer(id={self.id}, name='{self.name}', active={self.is_active})>"


class PrintJob(Base, TimestampMixin):
    """
    PrintJob model.

    Core job tracking based on Moonraker's job_history schema.
    """

    __tablename__ = "print_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    printer_id = Column(
        Integer,
        ForeignKey("printers.id", ondelete="CASCADE"),
        nullable=False
    )
    job_id = Column(String(100), nullable=False)  # Moonraker's UUID
    user = Column(String(100), nullable=True)
    filename = Column(String(500), nullable=False)
    title = Column(String(500), nullable=True)
    url = Column(String(1000), nullable=True)
    status = Column(String(50), nullable=False, index=True)  # completed, error, cancelled, printing, paused

    start_time = Column(UTCDateTime(), nullable=False, index=True)
    end_time = Column(UTCDateTime(), nullable=True)
    print_duration = Column(Float, nullable=True)  # Seconds
    total_duration = Column(Float, nullable=True)  # Seconds
    filament_used = Column(Float, nullable=True)   # Millimeters

    # JSON columns for flexible metadata
    job_metadata = Column(JSON, nullable=True)      # Moonraker metadata
    auxiliary_data = Column(JSON, nullable=True)    # Additional tracking

    # Relationships
    printer = relationship("Printer", back_populates="print_jobs")
    job_details = relationship(
        "JobDetails",
        back_populates="print_job",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Composite unique constraint and indexes
    __table_args__ = (
        Index('idx_printer_job', 'printer_id', 'job_id', unique=True),
        Index('idx_printer_status', 'printer_id', 'status'),
    )

    def __repr__(self) -> str:
        return f"<PrintJob(id={self.id}, printer_id={self.printer_id}, filename='{self.filename}', status='{self.status}')>"


class JobDetails(Base, TimestampMixin):
    """
    JobDetails model.

    Extended metadata from slicer gcode files (OrcaSlicer, etc.).
    """

    __tablename__ = "job_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    print_job_id = Column(
        Integer,
        ForeignKey("print_jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

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

    # Slicer information (Issue #5)
    slicer_name = Column(String(100), nullable=True)
    slicer_version = Column(String(50), nullable=True)

    # Print statistics
    estimated_time = Column(Integer, nullable=True)      # Seconds
    estimated_filament = Column(Float, nullable=True)    # Grams
    layer_count = Column(Integer, nullable=True)
    object_height = Column(Float, nullable=True)         # mm

    # Multi-filament usage and cost (Issue #5)
    filament_used_mm = Column(JSON, nullable=True)       # Array per-extruder
    filament_used_cm3 = Column(JSON, nullable=True)      # Array per-extruder
    filament_used_g = Column(JSON, nullable=True)        # Array per-extruder
    filament_cost = Column(JSON, nullable=True)          # Array per-extruder
    total_filament_used_g = Column(Float, nullable=True)  # Total across all
    total_filament_cost = Column(Float, nullable=True)    # Total cost

    # Config block (Issue #5)
    config_block = Column(JSON, nullable=True)           # Full config as dict

    # Raw metadata storage
    raw_metadata = Column(JSON, nullable=True)

    # Thumbnail (base64 encoded PNG from gcode)
    thumbnail_base64 = Column(String(100000), nullable=True)

    # Relationships
    print_job = relationship("PrintJob", back_populates="job_details")

    def __repr__(self) -> str:
        return f"<JobDetails(id={self.id}, print_job_id={self.print_job_id}, filament_type='{self.filament_type}')>"


class JobTotals(Base):
    """
    JobTotals model.

    Aggregated statistics per printer.
    """

    __tablename__ = "job_totals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    printer_id = Column(
        Integer,
        ForeignKey("printers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    total_jobs = Column(Integer, default=0, nullable=False)
    total_time = Column(Float, default=0.0, nullable=False)        # Seconds (total_duration)
    total_print_time = Column(Float, default=0.0, nullable=False)  # Seconds (print_duration)
    total_filament_used = Column(Float, default=0.0, nullable=False)  # Millimeters
    longest_job = Column(Float, default=0.0, nullable=False)       # Seconds

    last_updated = Column(
        UTCDateTime(),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    printer = relationship("Printer", back_populates="job_totals")

    def __repr__(self) -> str:
        return f"<JobTotals(printer_id={self.printer_id}, total_jobs={self.total_jobs})>"


class ApiKey(Base, TimestampMixin):
    """
    ApiKey model.

    API key management for authentication.
    """

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hash
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for display
    name = Column(String(100), nullable=False)       # User-friendly identifier
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_used = Column(UTCDateTime(), nullable=True)
    expires_at = Column(UTCDateTime(), nullable=True)

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}', active={self.is_active})>"


class MaintenanceRecord(Base, TimestampMixin):
    """
    MaintenanceRecord model.

    Tracks printer maintenance and repair history (Issue #9).
    """

    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    printer_id = Column(
        Integer,
        ForeignKey("printers.id", ondelete="CASCADE"),
        nullable=False
    )
    date = Column(UTCDateTime(), nullable=False, index=True)
    done = Column(Boolean, default=False, nullable=False, index=True)
    category = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    cost = Column(Float, nullable=True)
    notes = Column(String(2000), nullable=True)

    # Relationships
    printer = relationship("Printer", back_populates="maintenance_records")

    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_printer_maintenance_date', 'printer_id', 'date'),
    )

    def __repr__(self) -> str:
        return f"<MaintenanceRecord(id={self.id}, printer_id={self.printer_id}, category='{self.category}', done={self.done})>"
