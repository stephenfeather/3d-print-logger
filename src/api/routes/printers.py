"""
Printer CRUD endpoints for 3D Print Logger.

Provides REST API endpoints for managing printer configurations,
including create, read, update, delete, and status operations.
"""

import asyncio
import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from src.api.auth import get_api_key
from src.api.schemas import (
    JobResponse,
    PaginatedResponse,
    PrinterCreate,
    PrinterResponse,
    PrinterStatusResponse,
    PrinterUpdate,
)
from src.database.engine import get_db
from src.database.models import ApiKey, Printer, PrintJob
from src.moonraker.history import import_printer_history

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[PrinterResponse])
async def list_printers(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> List[PrinterResponse]:
    """List all printers.

    Args:
        include_inactive: If True, include inactive printers in the response.
    """
    query = db.query(Printer)
    if not include_inactive:
        query = query.filter(Printer.is_active == True)
    printers = query.all()
    return [PrinterResponse.model_validate(p) for p in printers]


async def _background_import_history(printer_id: int, moonraker_url: str) -> None:
    """Background task to import history after printer creation."""
    from src.database.engine import get_session_local

    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        stats = await import_printer_history(
            db=db,
            printer_id=printer_id,
            moonraker_url=moonraker_url,
            limit=1000,
        )
        logger.info(f"Background import for printer {printer_id}: {stats}")
    except Exception as e:
        logger.error(f"Background import failed for printer {printer_id}: {e}")
    finally:
        db.close()


@router.post("", response_model=PrinterResponse, status_code=status.HTTP_201_CREATED)
async def create_printer(
    printer_data: PrinterCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PrinterResponse:
    """Create a new printer.

    After creation, automatically imports job history from Moonraker
    in the background.
    """
    # Check for duplicate name
    existing = db.query(Printer).filter(Printer.name == printer_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Printer with name '{printer_data.name}' already exists",
        )

    printer = Printer(
        name=printer_data.name,
        moonraker_url=printer_data.moonraker_url,
        location=printer_data.location,
        moonraker_api_key=printer_data.moonraker_api_key,
        is_active=True,
    )
    db.add(printer)
    db.commit()
    db.refresh(printer)

    # Trigger background history import if Moonraker URL is configured
    if printer.moonraker_url:
        background_tasks.add_task(
            _background_import_history,
            printer.id,
            printer.moonraker_url,
        )
        logger.info(f"Queued background history import for printer {printer.id}")

    return PrinterResponse.model_validate(printer)


@router.get("/{printer_id}", response_model=PrinterResponse)
async def get_printer(
    printer_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PrinterResponse:
    """Get a printer by ID."""
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with id {printer_id} not found",
        )
    return PrinterResponse.model_validate(printer)


@router.put("/{printer_id}", response_model=PrinterResponse)
async def update_printer(
    printer_id: int,
    printer_data: PrinterUpdate,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PrinterResponse:
    """Update an existing printer."""
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with id {printer_id} not found",
        )

    # Check for duplicate name if name is being changed
    if printer_data.name is not None and printer_data.name != printer.name:
        existing = db.query(Printer).filter(Printer.name == printer_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Printer with name '{printer_data.name}' already exists",
            )

    # Update only provided fields
    update_data = printer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(printer, field, value)

    db.commit()
    db.refresh(printer)
    return PrinterResponse.model_validate(printer)


@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_printer(
    printer_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> None:
    """Delete a printer."""
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with id {printer_id} not found",
        )

    db.delete(printer)
    db.commit()


@router.get("/{printer_id}/status", response_model=PrinterStatusResponse)
async def get_printer_status(
    printer_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PrinterStatusResponse:
    """Get the current status of a printer.

    This returns the cached status from the database.
    For real-time status, use the WebSocket endpoint.
    """
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with id {printer_id} not found",
        )

    # Return status based on available data
    # In future, this will integrate with the Moonraker manager
    return PrinterStatusResponse(
        printer_id=printer.id,
        name=printer.name,
        is_connected=printer.last_seen is not None,
        state=None,  # Would come from live Moonraker connection
        progress=None,
        current_file=None,
        error=None,
    )


@router.get("/{printer_id}/jobs", response_model=PaginatedResponse[JobResponse])
async def get_printer_jobs(
    printer_id: int,
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PaginatedResponse[JobResponse]:
    """Get all jobs for a specific printer."""
    # Verify printer exists
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with id {printer_id} not found",
        )

    # Query jobs for this printer
    query = db.query(PrintJob).filter(PrintJob.printer_id == printer_id)
    total = query.count()

    jobs = (
        query.order_by(PrintJob.start_time.desc()).offset(offset).limit(limit).all()
    )

    # Convert to response format
    items = [
        JobResponse(
            id=job.id,
            printer_id=job.printer_id,
            job_id=job.job_id,
            user=job.user,
            filename=job.filename,
            status=job.status,
            start_time=job.start_time,
            end_time=job.end_time,
            print_duration=job.print_duration,
            total_duration=job.total_duration,
            filament_used=job.filament_used,
            job_metadata=job.job_metadata,
            created_at=job.created_at,
            updated_at=job.updated_at,
            details=None,
        )
        for job in jobs
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(jobs)) < total,
    )


@router.post("/{printer_id}/import-history")
async def import_history(
    printer_id: int,
    limit: int = Query(1000, ge=1, le=10000, description="Maximum jobs to import"),
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> dict:
    """Import job history from Moonraker for a printer.

    Fetches historical job data from the printer's Moonraker instance
    and imports it into the database. Existing jobs are updated, new
    jobs are created. This operation is idempotent.

    Args:
        printer_id: ID of the printer to import history for
        limit: Maximum number of jobs to import (default 1000)

    Returns:
        Dictionary with import statistics: imported, updated, skipped, errors
    """
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with id {printer_id} not found",
        )

    if not printer.moonraker_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Printer has no Moonraker URL configured",
        )

    try:
        stats = await import_printer_history(
            db=db,
            printer_id=printer_id,
            moonraker_url=printer.moonraker_url,
            limit=limit,
        )
        return {
            "printer_id": printer_id,
            "printer_name": printer.name,
            **stats,
        }
    except Exception as e:
        logger.error(f"Error importing history for printer {printer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to import history from Moonraker: {str(e)}",
        )
