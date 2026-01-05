"""
Job query endpoints for 3D Print Logger.

Provides REST API endpoints for querying print jobs,
including filtering by printer, status, and date range.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from src.api.auth import get_api_key
from src.api.schemas import (
    JobDetailsResponse,
    JobResponse,
    PaginatedResponse,
)
from src.database.engine import get_db
from src.database.models import ApiKey, JobDetails, Printer, PrintJob

router = APIRouter()


def _job_to_response(job: PrintJob) -> JobResponse:
    """Convert PrintJob ORM model to response schema."""
    details = None
    if job.job_details:
        details = JobDetailsResponse.model_validate(job.job_details)

    return JobResponse(
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
        details=details,
    )


@router.get("", response_model=PaginatedResponse[JobResponse])
async def list_jobs(
    printer_id: Optional[int] = Query(None, description="Filter by printer ID"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by job status"
    ),
    start_after: Optional[datetime] = Query(
        None, description="Filter jobs started after this time"
    ),
    start_before: Optional[datetime] = Query(
        None, description="Filter jobs started before this time"
    ),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PaginatedResponse[JobResponse]:
    """List all print jobs with optional filtering and pagination."""
    query = db.query(PrintJob).options(joinedload(PrintJob.job_details))

    # Apply filters
    if printer_id is not None:
        query = query.filter(PrintJob.printer_id == printer_id)
    if status_filter is not None:
        query = query.filter(PrintJob.status == status_filter)
    if start_after is not None:
        query = query.filter(PrintJob.start_time >= start_after)
    if start_before is not None:
        query = query.filter(PrintJob.start_time <= start_before)

    # Get total count before pagination
    total = query.count()

    # Apply pagination and ordering
    jobs = (
        query.order_by(PrintJob.start_time.desc()).offset(offset).limit(limit).all()
    )

    return PaginatedResponse(
        items=[_job_to_response(job) for job in jobs],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(jobs)) < total,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> JobResponse:
    """Get a print job by ID."""
    job = (
        db.query(PrintJob)
        .options(joinedload(PrintJob.job_details))
        .filter(PrintJob.id == job_id)
        .first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found",
        )
    return _job_to_response(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> None:
    """Delete a print job."""
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found",
        )

    db.delete(job)
    db.commit()
