"""
Event handlers for Moonraker notifications.

Processes Moonraker events such as job status updates,
history changes, and printer state changes.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.database.crud import (
    upsert_print_job,
    update_job_totals,
    update_printer_last_seen,
    update_active_job_metrics,
)
from src.database.engine import get_session_local
from src.database.models import PrintJob

logger = logging.getLogger(__name__)


def _strip_cache_path(filename: str) -> str:
    """
    Strip .cache/ directory prefix from filename.

    Since all files on Moonraker printers are stored in .cache/,
    this prefix is redundant and can be removed for cleaner display.

    Args:
        filename: Original filename (may include .cache/ prefix)

    Returns:
        Cleaned filename without .cache/ prefix

    Examples:
        >>> _strip_cache_path(".cache/test.gcode")
        'test.gcode'
        >>> _strip_cache_path("test.gcode")
        'test.gcode'
    """
    if filename.startswith(".cache/"):
        return filename[7:]  # Remove ".cache/" (7 characters)
    return filename


def _get_db_session() -> Session:
    """
    Get a database session for event handlers.

    Returns:
        Database session
    """
    SessionLocal = get_session_local()
    return SessionLocal()


async def handle_status_update(
    printer_id: int, params, db: Optional[Session] = None
) -> None:
    """
    Handle print_stats status update event.

    Updates PrintJob records based on printer state (printing, paused,
    completed, error). Creates new jobs or updates existing ones.

    Args:
        printer_id: ID of printer sending event
        params: Event parameters - list [objects_dict, eventtime] from Moonraker
        db: Optional database session (will create if not provided)
    """
    should_close_db = False
    if db is None:
        db = _get_db_session()
        should_close_db = True

    try:
        # Moonraker sends params as [objects_dict, eventtime]
        if isinstance(params, list) and len(params) > 0:
            objects = params[0]
        elif isinstance(params, dict):
            objects = params
        else:
            logger.warning(f"Unexpected params type for printer {printer_id}: {type(params)}")
            return

        print_stats = objects.get("print_stats", {})
        state = print_stats.get("state")
        print_duration = print_stats.get("print_duration")
        filament_used = print_stats.get("filament_used")

        if not state:
            # No state change - just metric updates during printing
            # Update the active job's metrics if we have any
            if print_duration is not None or filament_used is not None:
                update_active_job_metrics(
                    db,
                    printer_id,
                    print_duration or 0.0,
                    filament_used or 0.0,
                )
                # Also update printer last_seen
                update_printer_last_seen(db, printer_id)
            return

        filename = _strip_cache_path(print_stats.get("filename", "unknown"))
        print_duration = print_duration or 0.0
        filament_used = filament_used or 0.0

        logger.debug(
            f"Printer {printer_id} status: {state} - {filename}"
        )

        # Handle state transitions
        if state == "printing":
            # Create or update active job
            await _handle_printing_state(
                printer_id, filename, print_duration, filament_used, db
            )

        elif state == "paused":
            # Update job status to paused
            await _handle_paused_state(
                printer_id, filename, print_duration, filament_used, db
            )

        elif state in ["complete", "error"]:
            # Finalize job
            await _handle_completion_state(
                printer_id, state, filename, print_duration, filament_used, db
            )

        elif state == "standby":
            # Idle state - clean up any stale printing jobs
            await _handle_standby_state(printer_id, db)
            logger.debug(f"Printer {printer_id} is on standby")

        else:
            logger.warning(f"Unknown state '{state}' for printer {printer_id}")

        # Update printer last_seen timestamp
        update_printer_last_seen(db, printer_id)

    except Exception as e:
        logger.error(
            f"Error handling status update for printer {printer_id}: {e}"
        )

    finally:
        if should_close_db:
            db.close()


async def handle_history_changed(
    printer_id: int, params, db: Optional[Session] = None
) -> None:
    """
    Handle job_history notification from Moonraker.

    Syncs jobs from Moonraker's history (completed, deleted, etc.).

    Args:
        printer_id: ID of printer sending event
        params: Event parameters - can be list [data_dict] or dict from Moonraker
        db: Optional database session (will create if not provided)
    """
    should_close_db = False
    if db is None:
        db = _get_db_session()
        should_close_db = True

    try:
        # Moonraker may send params as [data_dict] or as data_dict directly
        if isinstance(params, list) and len(params) > 0:
            data = params[0]
        elif isinstance(params, dict):
            data = params
        else:
            logger.warning(f"Unexpected params type for printer {printer_id} history: {type(params)}")
            return

        action = data.get("action")
        job = data.get("job", {})

        if not action or not job:
            logger.debug(f"Missing action or job in history change for printer {printer_id}")
            return

        logger.debug(f"Printer {printer_id} history action: {action}")

        if action == "finished":
            await _sync_finished_job(printer_id, job, db)

        elif action == "added":
            await _sync_added_job(printer_id, job, db)

        elif action == "deleted":
            logger.debug(
                f"Job {job.get('job_id')} deleted from printer {printer_id}"
            )

        else:
            logger.debug(
                f"Unknown history action '{action}' for printer {printer_id}"
            )

        # Update printer last_seen timestamp
        update_printer_last_seen(db, printer_id)

    except Exception as e:
        logger.error(
            f"Error handling history change for printer {printer_id}: {e}"
        )

    finally:
        if should_close_db:
            db.close()


async def _handle_printing_state(
    printer_id: int,
    filename: str,
    print_duration: float,
    filament_used: float,
    db: Session,
) -> None:
    """
    Handle printing state - create or update active job.

    First checks for an existing job (from history import or previous status
    updates) for this printer + filename. If found, updates its metrics.
    Otherwise creates a synthetic job.

    Args:
        printer_id: Printer ID
        filename: Current print filename
        print_duration: Current print duration in seconds
        filament_used: Current filament used in mm
        db: Database session
    """
    # First, check if there's already a printing job for this file
    # (could be from history import with real Moonraker job_id)
    existing_job = (
        db.query(PrintJob)
        .filter(
            PrintJob.printer_id == printer_id,
            PrintJob.filename == filename,
            PrintJob.status.in_(["printing", "paused"]),
        )
        .order_by(PrintJob.start_time.desc())
        .first()
    )

    if existing_job:
        # Update existing job's metrics
        existing_job.print_duration = print_duration
        existing_job.filament_used = filament_used
        existing_job.status = "printing"  # In case it was paused
        db.commit()
        logger.debug(f"Updated existing job {existing_job.id} for printer {printer_id}")
        return

    # No existing job - create a synthetic one
    job_id = f"active-{filename}-{printer_id}"

    job = upsert_print_job(
        db,
        printer_id=printer_id,
        job_id=job_id,
        filename=filename,
        status="printing",
        start_time=datetime.utcnow(),
        print_duration=print_duration,
        filament_used=filament_used,
    )

    logger.debug(f"Created synthetic printing job {job.id} for printer {printer_id}")


async def _handle_paused_state(
    printer_id: int,
    filename: str,
    print_duration: float,
    filament_used: float,
    db: Session,
) -> None:
    """
    Handle paused state - update job status.

    Args:
        printer_id: Printer ID
        filename: Current print filename
        print_duration: Current print duration in seconds
        filament_used: Current filament used in mm
        db: Database session
    """
    job_id = f"active-{filename}-{printer_id}"

    job = upsert_print_job(
        db,
        printer_id=printer_id,
        job_id=job_id,
        filename=filename,
        status="paused",
        start_time=datetime.utcnow(),
        print_duration=print_duration,
        filament_used=filament_used,
    )

    logger.debug(f"Updated job {job.id} to paused status")


async def _handle_completion_state(
    printer_id: int,
    state: str,
    filename: str,
    print_duration: float,
    filament_used: float,
    db: Session,
) -> None:
    """
    Handle completion/error state - finalize job.

    Args:
        printer_id: Printer ID
        state: Final state (complete or error)
        filename: Print filename
        print_duration: Total print duration in seconds
        filament_used: Total filament used in mm
        db: Database session
    """
    job_id = f"active-{filename}-{printer_id}"

    # Determine final status
    final_status = "completed" if state == "complete" else "error"

    job = upsert_print_job(
        db,
        printer_id=printer_id,
        job_id=job_id,
        filename=filename,
        status=final_status,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),
        print_duration=print_duration,
        filament_used=filament_used,
    )

    logger.info(
        f"Job {job.id} finalized with status {final_status} "
        f"for printer {printer_id}"
    )

    # Clean up any other stale "printing" jobs for this printer
    # A printer can only print one thing at a time, so any other
    # "printing" jobs must be orphaned/stale
    stale_jobs = (
        db.query(PrintJob)
        .filter(
            PrintJob.printer_id == printer_id,
            PrintJob.status.in_(["printing", "paused"]),
            PrintJob.id != job.id  # Don't mark the just-completed job
        )
        .all()
    )

    if stale_jobs:
        now = datetime.utcnow()
        for stale_job in stale_jobs:
            stale_job.status = "cancelled"
            stale_job.end_time = now
            logger.info(
                f"Cleaned up stale job {stale_job.id} ({stale_job.filename}) "
                f"while completing job {job.id}"
            )
        db.commit()

    # Update job totals for printer
    totals = update_job_totals(db, printer_id)
    logger.debug(
        f"Updated totals for printer {printer_id}: "
        f"{totals.total_jobs} jobs"
    )


async def _handle_standby_state(
    printer_id: int,
    db: Session,
) -> None:
    """
    Handle standby state - clean up any stale printing/paused jobs.

    When a printer enters standby, it means no print is active.
    Any jobs still marked as "printing" or "paused" are stale and
    should be marked as cancelled.

    Args:
        printer_id: Printer ID
        db: Database session
    """
    # Find any stale "printing" or "paused" jobs for this printer
    stale_jobs = (
        db.query(PrintJob)
        .filter(
            PrintJob.printer_id == printer_id,
            PrintJob.status.in_(["printing", "paused"])
        )
        .all()
    )

    if stale_jobs:
        now = datetime.utcnow()
        for job in stale_jobs:
            job.status = "cancelled"
            job.end_time = now
            logger.info(
                f"Cleaned up stale job {job.id} ({job.filename}) "
                f"for printer {printer_id} - marked as cancelled"
            )
        db.commit()
        logger.info(f"Cleaned up {len(stale_jobs)} stale jobs for printer {printer_id}")


async def _sync_finished_job(
    printer_id: int, job_data: dict, db: Session
) -> None:
    """
    Sync a finished job from Moonraker history.

    Args:
        printer_id: Printer ID
        job_data: Job data from history
        db: Database session
    """
    job_id = job_data.get("job_id", "unknown")
    filename = _strip_cache_path(job_data.get("filename", "unknown"))
    status = job_data.get("status", "completed")

    # Convert timestamp fields if present
    start_time = datetime.utcnow()
    if "start_time" in job_data and job_data["start_time"]:
        try:
            start_time = datetime.fromtimestamp(job_data["start_time"])
        except (ValueError, TypeError):
            pass

    end_time = datetime.utcnow()
    if "end_time" in job_data and job_data["end_time"]:
        try:
            end_time = datetime.fromtimestamp(job_data["end_time"])
        except (ValueError, TypeError):
            pass

    print_duration = job_data.get("print_duration", 0.0)
    total_duration = job_data.get("total_duration", 0.0)
    filament_used = job_data.get("filament_used", 0.0)

    job = upsert_print_job(
        db,
        printer_id=printer_id,
        job_id=job_id,
        filename=filename,
        status=status,
        start_time=start_time,
        end_time=end_time,
        print_duration=print_duration,
        total_duration=total_duration if total_duration else print_duration,
        filament_used=filament_used,
    )

    logger.info(
        f"Synced finished job {job.id} from history "
        f"for printer {printer_id}"
    )

    # Clean up any synthetic "printing" jobs with matching filename
    # This handles the case where status_update creates a synthetic job
    # and history_changed creates a real job with a different ID
    stale_jobs = (
        db.query(PrintJob)
        .filter(
            PrintJob.printer_id == printer_id,
            PrintJob.filename == filename,
            PrintJob.status.in_(["printing", "paused"]),
            PrintJob.job_id != job_id  # Don't mark the just-synced job
        )
        .all()
    )

    if stale_jobs:
        for stale_job in stale_jobs:
            stale_job.status = status  # Use same status as the real job
            stale_job.end_time = end_time
            stale_job.print_duration = print_duration
            stale_job.filament_used = filament_used
            logger.info(
                f"Cleaned up synthetic job {stale_job.id} ({stale_job.job_id}) "
                f"matching finished job {job_id}"
            )
        db.commit()


async def _sync_added_job(
    printer_id: int, job_data: dict, db: Session
) -> None:
    """
    Sync an added job from Moonraker history.

    Args:
        printer_id: Printer ID
        job_data: Job data from history
        db: Database session
    """
    job_id = job_data.get("job_id", "unknown")
    filename = _strip_cache_path(job_data.get("filename", "unknown"))

    start_time = datetime.utcnow()
    if "start_time" in job_data and job_data["start_time"]:
        try:
            start_time = datetime.fromtimestamp(job_data["start_time"])
        except (ValueError, TypeError):
            pass

    job = upsert_print_job(
        db,
        printer_id=printer_id,
        job_id=job_id,
        filename=filename,
        status="printing",
        start_time=start_time,
        print_duration=job_data.get("print_duration", 0.0),
        filament_used=job_data.get("filament_used", 0.0),
    )

    logger.debug(
        f"Synced added job {job.id} from history for printer {printer_id}"
    )
