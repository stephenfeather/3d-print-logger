"""
CRUD operations for 3D Print Logger database.

Provides Create, Read, Update, Delete operations for:
- Printer
- PrintJob
- JobDetails
- JobTotals
- ApiKey
"""

from datetime import datetime, UTC
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.database.models import ApiKey, JobDetails, JobTotals, MaintenanceRecord, Printer, PrintJob


# ========== Printer CRUD ==========


def get_printer(db: Session, printer_id: int) -> Optional[Printer]:
    """
    Get a printer by its ID.

    Args:
        db: Database session
        printer_id: Printer ID to look up

    Returns:
        Printer if found, None otherwise
    """
    return db.query(Printer).filter(Printer.id == printer_id).first()


def get_active_printers(db: Session) -> List[Printer]:
    """
    Get all active printers.

    Args:
        db: Database session

    Returns:
        List of active printers
    """
    return db.query(Printer).filter(Printer.is_active == True).all()


def create_printer(db: Session, name: str, moonraker_url: str, **kwargs) -> Printer:
    """
    Create a new printer.

    Args:
        db: Database session
        name: Printer name (unique)
        moonraker_url: Moonraker API URL
        **kwargs: Optional fields (location, moonraker_api_key, is_active)

    Returns:
        Created Printer instance
    """
    printer = Printer(name=name, moonraker_url=moonraker_url, **kwargs)
    db.add(printer)
    db.commit()
    db.refresh(printer)
    return printer


def update_printer_last_seen(db: Session, printer_id: int) -> None:
    """
    Update a printer's last_seen timestamp to current time.

    Args:
        db: Database session
        printer_id: Printer ID to update
    """
    db.query(Printer).filter(Printer.id == printer_id).update(
        {"last_seen": datetime.now(UTC)}
    )
    db.commit()


# ========== PrintJob CRUD ==========


def get_print_job(
    db: Session, printer_id: int, job_id: str
) -> Optional[PrintJob]:
    """
    Get a print job by printer_id and job_id.

    Args:
        db: Database session
        printer_id: Printer ID
        job_id: Moonraker's job UUID

    Returns:
        PrintJob if found, None otherwise
    """
    return db.query(PrintJob).filter(
        and_(PrintJob.printer_id == printer_id, PrintJob.job_id == job_id)
    ).first()


def upsert_print_job(
    db: Session, printer_id: int, job_id: str, **job_data
) -> PrintJob:
    """
    Insert or update a print job.

    Handles duplicate (printer_id, job_id) composite key by updating
    existing record or creating new one.

    Args:
        db: Database session
        printer_id: Foreign key to printer
        job_id: Moonraker's job UUID
        **job_data: Job fields (filename, status, start_time, end_time,
                    print_duration, total_duration, filament_used,
                    job_metadata, auxiliary_data)

    Returns:
        Created or updated PrintJob instance
    """
    job = db.query(PrintJob).filter(
        and_(PrintJob.printer_id == printer_id, PrintJob.job_id == job_id)
    ).first()

    if job:
        # Update existing job
        for key, value in job_data.items():
            setattr(job, key, value)
    else:
        # Create new job
        job = PrintJob(printer_id=printer_id, job_id=job_id, **job_data)
        db.add(job)

    db.commit()
    db.refresh(job)
    return job


def get_jobs_by_printer(
    db: Session, printer_id: int, status: Optional[str] = None
) -> List[PrintJob]:
    """
    Get all print jobs for a printer, optionally filtered by status.

    Args:
        db: Database session
        printer_id: Printer ID to get jobs for
        status: Optional status filter (completed, error, cancelled, etc.)

    Returns:
        List of PrintJob instances, ordered by start_time descending
    """
    query = db.query(PrintJob).filter(PrintJob.printer_id == printer_id)
    if status:
        query = query.filter(PrintJob.status == status)
    return query.order_by(PrintJob.start_time.desc()).all()


def update_active_job_metrics(
    db: Session,
    printer_id: int,
    print_duration: float,
    filament_used: float,
) -> Optional[PrintJob]:
    """
    Update metrics for an active printing job.

    Finds the most recent "printing" or "paused" job for the printer
    and updates its duration and filament usage.

    Args:
        db: Database session
        printer_id: Printer ID
        print_duration: Current print duration in seconds
        filament_used: Current filament used in mm

    Returns:
        Updated PrintJob if found, None otherwise
    """
    # Find active job (most recent printing/paused)
    job = (
        db.query(PrintJob)
        .filter(
            PrintJob.printer_id == printer_id,
            PrintJob.status.in_(["printing", "paused"]),
        )
        .order_by(PrintJob.start_time.desc())
        .first()
    )

    if job:
        job.print_duration = print_duration
        job.filament_used = filament_used
        db.commit()

    return job


# ========== JobTotals Management ==========


def update_job_totals(db: Session, printer_id: int) -> JobTotals:
    """
    Recalculate and update job totals for a printer.

    Creates a new JobTotals record if one doesn't exist.
    Aggregates statistics from all completed jobs.

    Args:
        db: Database session
        printer_id: Printer ID to calculate totals for

    Returns:
        Updated JobTotals instance
    """
    # Get or create totals record
    totals = db.query(JobTotals).filter(JobTotals.printer_id == printer_id).first()
    if not totals:
        totals = JobTotals(printer_id=printer_id)
        db.add(totals)

    # Aggregate from completed jobs only
    completed_jobs = db.query(PrintJob).filter(
        and_(PrintJob.printer_id == printer_id, PrintJob.status == "completed")
    ).all()

    totals.total_jobs = len(completed_jobs)
    totals.total_time = sum(j.total_duration or 0 for j in completed_jobs)
    totals.total_print_time = sum(j.print_duration or 0 for j in completed_jobs)
    totals.total_filament_used = sum(j.filament_used or 0 for j in completed_jobs)
    totals.longest_job = max(
        (j.total_duration or 0 for j in completed_jobs), default=0
    )

    db.commit()
    db.refresh(totals)
    return totals


# ========== JobDetails CRUD ==========


def create_job_details(db: Session, print_job_id: int, **details_data) -> JobDetails:
    """
    Create job details for a print job.

    Stores extracted gcode metadata (slicer settings, estimates, etc.).

    Args:
        db: Database session
        print_job_id: Foreign key to print job
        **details_data: Detail fields (layer_height, nozzle_temp, filament_type, etc.)

    Returns:
        Created JobDetails instance
    """
    details = JobDetails(print_job_id=print_job_id, **details_data)
    db.add(details)
    db.commit()
    db.refresh(details)
    return details


def get_jobs_without_details(db: Session, printer_id: int) -> List[PrintJob]:
    """
    Get all print jobs for a printer that don't have job_details records.

    Useful for backfilling historical data.

    Args:
        db: Database session
        printer_id: Printer ID to get jobs for

    Returns:
        List of PrintJob instances without job_details, ordered by start_time
    """
    return db.query(PrintJob).filter(
        and_(
            PrintJob.printer_id == printer_id,
            ~PrintJob.id.in_(
                db.query(JobDetails.print_job_id)
            )
        )
    ).order_by(PrintJob.start_time).all()


# ========== ApiKey Management ==========


def create_api_key(
    db: Session, key_hash: str, key_prefix: str, name: str, **kwargs
) -> ApiKey:
    """
    Create a new API key.

    Args:
        db: Database session
        key_hash: SHA-256 hash of the key (never store plaintext)
        key_prefix: First 8 chars for user identification
        name: User-friendly name for the key
        **kwargs: Optional fields (is_active, expires_at)

    Returns:
        Created ApiKey instance
    """
    api_key = ApiKey(key_hash=key_hash, key_prefix=key_prefix, name=name, **kwargs)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


def get_api_key_by_hash(db: Session, key_hash: str) -> Optional[ApiKey]:
    """
    Look up an API key by its hash.

    Only returns active keys.

    Args:
        db: Database session
        key_hash: SHA-256 hash to look up

    Returns:
        ApiKey if found and active, None otherwise
    """
    return db.query(ApiKey).filter(
        and_(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    ).first()


def update_api_key_last_used(db: Session, api_key_id: int) -> None:
    """
    Update an API key's last_used timestamp to current time.

    Args:
        db: Database session
        api_key_id: API key ID to update
    """
    db.query(ApiKey).filter(ApiKey.id == api_key_id).update(
        {"last_used": datetime.now(UTC)}
    )
    db.commit()


# ========== MaintenanceRecord CRUD ==========


def create_maintenance_record(
    db: Session,
    printer_id: int,
    date: datetime,
    category: str,
    description: str,
    **kwargs
) -> MaintenanceRecord:
    """
    Create a new maintenance record.

    Args:
        db: Database session
        printer_id: Foreign key to printer
        date: Date when maintenance was performed
        category: Category of maintenance (cleaning, calibration, repair, etc.)
        description: Description of what was done
        **kwargs: Optional fields (done, cost, notes)

    Returns:
        Created MaintenanceRecord instance
    """
    record = MaintenanceRecord(
        printer_id=printer_id,
        date=date,
        category=category,
        description=description,
        **kwargs
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_maintenance_record(db: Session, record_id: int) -> Optional[MaintenanceRecord]:
    """
    Get a maintenance record by its ID.

    Args:
        db: Database session
        record_id: Maintenance record ID to look up

    Returns:
        MaintenanceRecord if found, None otherwise
    """
    return db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()


def get_maintenance_records(
    db: Session,
    printer_id: Optional[int] = None,
    done: Optional[bool] = None
) -> List[MaintenanceRecord]:
    """
    Get maintenance records, optionally filtered by printer and/or completion status.

    Args:
        db: Database session
        printer_id: Optional filter by printer ID
        done: Optional filter by completion status

    Returns:
        List of MaintenanceRecord instances, ordered by date descending
    """
    query = db.query(MaintenanceRecord)

    if printer_id is not None:
        query = query.filter(MaintenanceRecord.printer_id == printer_id)
    if done is not None:
        query = query.filter(MaintenanceRecord.done == done)

    return query.order_by(MaintenanceRecord.date.desc()).all()


def update_maintenance_record(
    db: Session, record_id: int, **kwargs
) -> Optional[MaintenanceRecord]:
    """
    Update a maintenance record.

    Args:
        db: Database session
        record_id: Maintenance record ID to update
        **kwargs: Fields to update (date, category, description, done, cost, notes)

    Returns:
        Updated MaintenanceRecord if found, None otherwise
    """
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()

    if not record:
        return None

    for key, value in kwargs.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


def delete_maintenance_record(db: Session, record_id: int) -> bool:
    """
    Delete a maintenance record.

    Args:
        db: Database session
        record_id: Maintenance record ID to delete

    Returns:
        True if deleted, False if not found
    """
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()

    if not record:
        return False

    db.delete(record)
    db.commit()
    return True
