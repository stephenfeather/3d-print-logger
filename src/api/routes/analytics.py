"""
Analytics endpoints for 3D Print Logger.

Provides REST API endpoints for dashboard analytics,
including summary statistics, filament usage, and timeline data.
"""

from collections import defaultdict
from typing import List, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.auth import get_api_key
from src.api.schemas import (
    DashboardSummary,
    FilamentUsage,
    PrinterStats,
    TimelineEntry,
)
from src.database.engine import get_db
from src.database.models import ApiKey, JobDetails, Printer, PrintJob

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> DashboardSummary:
    """Get dashboard summary statistics."""
    # Total jobs count
    total_jobs = db.query(func.count(PrintJob.id)).scalar() or 0

    # Total print time (sum of print_duration)
    total_print_time = (
        db.query(func.coalesce(func.sum(PrintJob.print_duration), 0.0)).scalar() or 0.0
    )

    # Total filament used
    total_filament_used = (
        db.query(func.coalesce(func.sum(PrintJob.filament_used), 0.0)).scalar() or 0.0
    )

    # Successful jobs (status = 'completed')
    successful_jobs = (
        db.query(func.count(PrintJob.id))
        .filter(PrintJob.status == "completed")
        .scalar()
        or 0
    )

    # Failed jobs (status = 'error')
    failed_jobs = (
        db.query(func.count(PrintJob.id)).filter(PrintJob.status == "error").scalar()
        or 0
    )

    # Active printers count
    active_printers = (
        db.query(func.count(Printer.id)).filter(Printer.is_active == True).scalar()
        or 0
    )

    return DashboardSummary(
        total_jobs=total_jobs,
        total_print_time=total_print_time,
        total_filament_used=total_filament_used,
        successful_jobs=successful_jobs,
        failed_jobs=failed_jobs,
        active_printers=active_printers,
    )


@router.get("/printers", response_model=List[PrinterStats])
async def get_printer_stats(
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> List[PrinterStats]:
    """Get statistics per printer."""
    # Get all active printers with their job statistics
    printers = db.query(Printer).filter(Printer.is_active == True).all()

    stats = []
    for printer in printers:
        # Get job statistics for this printer
        job_stats = (
            db.query(
                func.count(PrintJob.id).label("total_jobs"),
                func.coalesce(func.sum(PrintJob.print_duration), 0.0).label(
                    "total_print_time"
                ),
                func.coalesce(func.sum(PrintJob.filament_used), 0.0).label(
                    "total_filament_used"
                ),
                func.max(PrintJob.start_time).label("last_job_at"),
            )
            .filter(PrintJob.printer_id == printer.id)
            .first()
        )

        successful = (
            db.query(func.count(PrintJob.id))
            .filter(PrintJob.printer_id == printer.id, PrintJob.status == "completed")
            .scalar()
            or 0
        )

        failed = (
            db.query(func.count(PrintJob.id))
            .filter(PrintJob.printer_id == printer.id, PrintJob.status == "error")
            .scalar()
            or 0
        )

        stats.append(
            PrinterStats(
                printer_id=printer.id,
                printer_name=printer.name,
                total_jobs=job_stats.total_jobs or 0,
                total_print_time=job_stats.total_print_time or 0.0,
                total_filament_used=job_stats.total_filament_used or 0.0,
                successful_jobs=successful,
                failed_jobs=failed,
                last_job_at=job_stats.last_job_at,
            )
        )

    return stats


@router.get("/filament", response_model=List[FilamentUsage])
async def get_filament_usage(
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> List[FilamentUsage]:
    """Get filament usage grouped by filament type."""
    # Query job details with filament type and sum the usage
    results = (
        db.query(
            JobDetails.filament_type,
            func.count(JobDetails.id).label("job_count"),
            func.coalesce(func.sum(PrintJob.filament_used), 0.0).label("total_used"),
        )
        .join(PrintJob, JobDetails.print_job_id == PrintJob.id)
        .filter(JobDetails.filament_type.isnot(None))
        .group_by(JobDetails.filament_type)
        .all()
    )

    return [
        FilamentUsage(
            filament_type=r.filament_type,
            total_used=r.total_used or 0.0,
            job_count=r.job_count or 0,
        )
        for r in results
    ]


@router.get("/timeline", response_model=List[TimelineEntry])
async def get_timeline(
    period: Literal["day", "week", "month"] = Query(
        "day", description="Time period grouping"
    ),
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> List[TimelineEntry]:
    """Get job timeline grouped by period."""
    jobs = db.query(PrintJob).filter(PrintJob.start_time.isnot(None)).all()

    if not jobs:
        return []

    # Group jobs by period
    timeline_data = defaultdict(
        lambda: {
            "job_count": 0,
            "total_print_time": 0.0,
            "successful_jobs": 0,
            "failed_jobs": 0,
        }
    )

    for job in jobs:
        if period == "day":
            period_key = job.start_time.strftime("%Y-%m-%d")
        elif period == "week":
            period_key = job.start_time.strftime("%Y-W%W")
        else:  # month
            period_key = job.start_time.strftime("%Y-%m")

        timeline_data[period_key]["job_count"] += 1
        timeline_data[period_key]["total_print_time"] += job.print_duration or 0.0

        if job.status == "completed":
            timeline_data[period_key]["successful_jobs"] += 1
        elif job.status == "error":
            timeline_data[period_key]["failed_jobs"] += 1

    # Convert to list and sort by period
    return [
        TimelineEntry(
            period=period_key,
            job_count=data["job_count"],
            total_print_time=data["total_print_time"],
            successful_jobs=data["successful_jobs"],
            failed_jobs=data["failed_jobs"],
        )
        for period_key, data in sorted(timeline_data.items())
    ]
