"""
Moonraker History Import Module

Functions for fetching and importing job history from Moonraker's REST API.
"""

import json
import logging
from datetime import datetime, UTC
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from sqlalchemy.orm import Session

from src.database.crud import (
    get_print_job,
    upsert_print_job,
    update_job_totals,
    create_job_details,
)
from src.gcode.parser import GcodeParser


logger = logging.getLogger(__name__)

# Singleton parser instance
_parser = GcodeParser()


def fetch_gcode_content(moonraker_url: str, filename: str) -> str | None:
    """
    Fetch gcode file content from Moonraker.

    Args:
        moonraker_url: Base URL of Moonraker instance
        filename: Name of the gcode file to fetch

    Returns:
        Gcode content as string, or None if fetch failed
    """
    base_url = moonraker_url.rstrip("/")

    # URL encode the filename (spaces -> %20, etc.)
    from urllib.parse import quote
    encoded_filename = quote(filename, safe="")

    url = f"{base_url}/server/files/gcodes/{encoded_filename}"

    try:
        request = Request(url)
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError) as e:
        logger.debug(f"Failed to fetch gcode {filename}: {e}")
        return None
    except Exception as e:
        logger.debug(f"Error fetching gcode {filename}: {e}")
        return None


async def fetch_moonraker_history(
    moonraker_url: str,
    limit: int = 1000,
    start: int = 0
) -> tuple[list[dict[str, Any]], int]:
    """
    Fetch job history from Moonraker's REST API.

    Args:
        moonraker_url: Base URL of Moonraker instance (e.g., http://10.1.1.211:7125)
        limit: Maximum number of jobs to fetch
        start: Offset for pagination

    Returns:
        Tuple of (list of job dictionaries, total count)
    """
    # Normalize URL (remove trailing slash)
    base_url = moonraker_url.rstrip("/")

    # Build history endpoint URL
    url = f"{base_url}/server/history/list?limit={limit}&start={start}"

    try:
        request = Request(url)
        request.add_header("Accept", "application/json")

        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode())

        result = data.get("result", {})
        jobs = result.get("jobs", [])
        total_count = result.get("count", len(jobs))

        logger.info(f"Fetched {len(jobs)} jobs from {moonraker_url} (total: {total_count})")
        return jobs, total_count

    except HTTPError as e:
        logger.error(f"HTTP error fetching history from {moonraker_url}: {e.code} {e.reason}")
        raise
    except URLError as e:
        logger.error(f"URL error fetching history from {moonraker_url}: {e.reason}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error from {moonraker_url}: {e}")
        raise


def _convert_timestamp(unix_ts: float | None) -> datetime | None:
    """Convert Unix timestamp to datetime, returning None if invalid."""
    if unix_ts is None:
        return None
    try:
        return datetime.fromtimestamp(unix_ts, tz=UTC).replace(tzinfo=None)
    except (ValueError, TypeError, OSError):
        return None


def import_job_from_moonraker(
    db: Session,
    printer_id: int,
    job_data: dict[str, Any],
    moonraker_url: str | None = None
) -> tuple[bool, str]:
    """
    Import a single job from Moonraker history data.

    Args:
        db: Database session
        printer_id: ID of the printer
        job_data: Job dictionary from Moonraker history API
        moonraker_url: Optional Moonraker URL for fetching gcode (for thumbnails)

    Returns:
        Tuple of (was_imported: bool, reason: str)
        - (True, "imported") - New job created
        - (True, "updated") - Existing job updated
        - (False, "skipped") - Job already exists and unchanged
        - (False, "error: ...") - Error occurred
    """
    job_id = job_data.get("job_id")
    if not job_id:
        return False, "error: missing job_id"

    filename = job_data.get("filename", "unknown")

    # Check if job already exists
    existing = get_print_job(db, printer_id, job_id)

    # Parse timestamps
    start_time = _convert_timestamp(job_data.get("start_time"))
    end_time = _convert_timestamp(job_data.get("end_time"))

    # Use current time as fallback for start_time
    if start_time is None:
        start_time = datetime.now(UTC).replace(tzinfo=None)

    # Determine status
    status = job_data.get("status", "completed")
    if status == "in_progress":
        status = "printing"

    # Build job record
    job_record = {
        "filename": filename,
        "status": status,
        "start_time": start_time,
        "end_time": end_time,
        "print_duration": job_data.get("print_duration", 0.0),
        "total_duration": job_data.get("total_duration") or job_data.get("print_duration", 0.0),
        "filament_used": job_data.get("filament_used", 0.0),
        "job_metadata": job_data.get("metadata", {}),
    }

    try:
        print_job = upsert_print_job(db, printer_id, job_id, **job_record)

        # Fetch and parse gcode for thumbnail extraction (only for new jobs)
        if not existing and moonraker_url and print_job:
            gcode_content = fetch_gcode_content(moonraker_url, filename)
            if gcode_content:
                try:
                    metadata = _parser.parse(gcode_content)
                    details_data = metadata.to_dict()

                    # Remove raw_metadata (stored separately)
                    details_data.pop("raw_metadata", None)

                    create_job_details(db, print_job.id, **details_data)
                    logger.debug(f"Created job details with thumbnail for {filename}")
                except Exception as e:
                    logger.debug(f"Failed to parse gcode for {filename}: {e}")

        if existing:
            return True, "updated"
        return True, "imported"

    except Exception as e:
        logger.error(f"Error importing job {job_id}: {e}")
        return False, f"error: {str(e)}"


async def import_printer_history(
    db: Session,
    printer_id: int,
    moonraker_url: str,
    limit: int = 1000
) -> dict[str, int]:
    """
    Import all job history from a Moonraker instance.

    Args:
        db: Database session
        printer_id: ID of the printer to import for
        moonraker_url: Moonraker base URL
        limit: Maximum jobs to import

    Returns:
        Dictionary with counts: {"imported": N, "updated": N, "skipped": N, "errors": N}
    """
    stats = {"imported": 0, "updated": 0, "skipped": 0, "errors": 0}

    try:
        jobs, total = await fetch_moonraker_history(moonraker_url, limit=limit)
    except Exception as e:
        logger.error(f"Failed to fetch history for printer {printer_id}: {e}")
        return {"imported": 0, "updated": 0, "skipped": 0, "errors": 1}

    logger.info(f"Importing {len(jobs)} jobs for printer {printer_id}")

    for job_data in jobs:
        success, reason = import_job_from_moonraker(
            db, printer_id, job_data, moonraker_url=moonraker_url
        )

        if reason == "imported":
            stats["imported"] += 1
        elif reason == "updated":
            stats["updated"] += 1
        elif reason == "skipped":
            stats["skipped"] += 1
        else:
            stats["errors"] += 1

    # Update job totals after import
    if stats["imported"] > 0 or stats["updated"] > 0:
        update_job_totals(db, printer_id)

    logger.info(
        f"Import complete for printer {printer_id}: "
        f"{stats['imported']} imported, {stats['updated']} updated, "
        f"{stats['skipped']} skipped, {stats['errors']} errors"
    )

    return stats


async def backfill_job_details(
    db: Session,
    printer_id: int,
    moonraker_url: str
) -> dict[str, int]:
    """
    Backfill job_details for jobs that don't have them yet.

    This is useful for historical jobs that were imported before the
    gcode parsing feature was implemented.

    Args:
        db: Database session
        printer_id: ID of the printer
        moonraker_url: Moonraker base URL to fetch gcode files

    Returns:
        Dictionary with counts: {"processed": N, "created": N, "errors": N}
    """
    from src.database.crud import get_jobs_without_details

    stats = {"processed": 0, "created": 0, "errors": 0}

    # Find all jobs without job_details
    jobs_without_details = get_jobs_without_details(db, printer_id)

    logger.info(f"Found {len(jobs_without_details)} jobs without details for printer {printer_id}")

    for job in jobs_without_details:
        stats["processed"] += 1

        # Fetch gcode content
        gcode_content = fetch_gcode_content(moonraker_url, job.filename)
        if not gcode_content:
            logger.debug(f"Could not fetch gcode for {job.filename}")
            stats["errors"] += 1
            continue

        # Parse and create job_details
        try:
            metadata = _parser.parse(gcode_content)
            details_data = metadata.to_dict()

            # Remove raw_metadata (stored separately)
            details_data.pop("raw_metadata", None)

            create_job_details(db, job.id, **details_data)
            stats["created"] += 1
            logger.debug(f"Created job details for {job.filename}")
        except Exception as e:
            logger.error(f"Failed to parse/create details for {job.filename}: {e}")
            stats["errors"] += 1

    logger.info(
        f"Backfill complete for printer {printer_id}: "
        f"{stats['processed']} processed, {stats['created']} created, "
        f"{stats['errors']} errors"
    )

    return stats
