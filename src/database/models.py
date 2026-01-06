"""
SQLAlchemy ORM models for 3D Print Logger.

Defines the database schema for printers, print jobs, job details,
job totals, and API keys. Supports both SQLite and MySQL 8.
"""

from datetime import datetime
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
)
from sqlalchemy.orm import relationship

from src.database.engine import Base


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at columns.
    Works with both SQLite and MySQL.
    """

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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
    last_seen = Column(DateTime, nullable=True)

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
    status = Column(String(50), nullable=False, index=True)  # completed, error, cancelled, printing, paused

    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
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

    # Print statistics
    estimated_time = Column(Integer, nullable=True)      # Seconds
    estimated_filament = Column(Float, nullable=True)    # Grams
    layer_count = Column(Integer, nullable=True)
    object_height = Column(Float, nullable=True)         # mm

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
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}', active={self.is_active})>"
