"""
Tests for CRUD operations in src/database/crud.py.

Tests follow TDD approach - written before implementation.
Covers all CRUD operations for:
- Printer
- PrintJob
- JobDetails
- JobTotals
- ApiKey
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

# These imports will fail until crud.py is implemented
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
from src.database.models import Printer, PrintJob, JobDetails, JobTotals, ApiKey


# ========== Printer CRUD Tests ==========

class TestPrinterCRUD:
    """Test Printer CRUD operations."""

    def test_create_printer(self, db_session):
        """Test creating a new printer."""
        printer = create_printer(
            db_session,
            name="Test Printer",
            moonraker_url="http://localhost:7125"
        )

        assert printer.id is not None
        assert printer.name == "Test Printer"
        assert printer.moonraker_url == "http://localhost:7125"
        assert printer.is_active is True  # Default value
        assert printer.created_at is not None
        assert printer.updated_at is not None

    def test_create_printer_with_optional_fields(self, db_session):
        """Test creating a printer with optional fields."""
        printer = create_printer(
            db_session,
            name="Full Printer",
            moonraker_url="http://printer.local:7125",
            location="Lab Room 1",
            moonraker_api_key="secret-key-123",
            is_active=False
        )

        assert printer.name == "Full Printer"
        assert printer.location == "Lab Room 1"
        assert printer.moonraker_api_key == "secret-key-123"
        assert printer.is_active is False

    def test_get_printer_exists(self, db_session):
        """Test getting an existing printer by ID."""
        created = create_printer(
            db_session,
            name="Printer To Get",
            moonraker_url="http://localhost:7125"
        )

        fetched = get_printer(db_session, created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Printer To Get"

    def test_get_printer_not_exists(self, db_session):
        """Test getting a non-existent printer returns None."""
        result = get_printer(db_session, 99999)

        assert result is None

    def test_get_active_printers_filters_inactive(self, db_session):
        """Test get_active_printers only returns active printers."""
        # Create active printers
        active1 = create_printer(
            db_session,
            name="Active 1",
            moonraker_url="http://active1.local:7125",
            is_active=True
        )
        active2 = create_printer(
            db_session,
            name="Active 2",
            moonraker_url="http://active2.local:7125",
            is_active=True
        )

        # Create inactive printer
        inactive = create_printer(
            db_session,
            name="Inactive",
            moonraker_url="http://inactive.local:7125",
            is_active=False
        )

        active_printers = get_active_printers(db_session)

        assert len(active_printers) == 2
        active_ids = [p.id for p in active_printers]
        assert active1.id in active_ids
        assert active2.id in active_ids
        assert inactive.id not in active_ids

    def test_get_active_printers_empty(self, db_session):
        """Test get_active_printers returns empty list when none active."""
        # Create only inactive printers
        create_printer(
            db_session,
            name="Inactive 1",
            moonraker_url="http://inactive1.local:7125",
            is_active=False
        )

        active_printers = get_active_printers(db_session)

        assert active_printers == []

    def test_update_printer_last_seen(self, db_session):
        """Test updating printer last_seen timestamp."""
        printer = create_printer(
            db_session,
            name="Ping Printer",
            moonraker_url="http://localhost:7125"
        )

        # Initially last_seen should be None
        assert printer.last_seen is None

        # Update last_seen
        update_printer_last_seen(db_session, printer.id)

        # Refresh to get updated value
        db_session.refresh(printer)

        assert printer.last_seen is not None
        # Verify it's recent (within last minute)
        time_diff = datetime.utcnow() - printer.last_seen
        assert time_diff.total_seconds() < 60


# ========== PrintJob CRUD Tests ==========

class TestPrintJobCRUD:
    """Test PrintJob CRUD operations."""

    def test_upsert_print_job_creates_new(self, db_session, sample_printer):
        """Test upsert creates a new job when none exists."""
        job = upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="new-job-123",
            filename="test_print.gcode",
            status="printing",
            start_time=datetime.utcnow()
        )

        assert job.id is not None
        assert job.printer_id == sample_printer.id
        assert job.job_id == "new-job-123"
        assert job.filename == "test_print.gcode"
        assert job.status == "printing"

    def test_upsert_print_job_updates_existing(self, db_session, sample_printer):
        """Test upsert updates existing job with same (printer_id, job_id)."""
        start_time = datetime.utcnow()

        # Create initial job
        job1 = upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="job-to-update",
            filename="test.gcode",
            status="printing",
            start_time=start_time
        )
        original_id = job1.id

        # Update the same job (same printer_id + job_id)
        end_time = datetime.utcnow()
        job2 = upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="job-to-update",
            status="completed",
            end_time=end_time,
            print_duration=3600.0,
            total_duration=3700.0,
            filament_used=15000.0
        )

        # Should be the same record
        assert job2.id == original_id
        # Should have updated fields
        assert job2.status == "completed"
        assert job2.end_time == end_time
        assert job2.print_duration == 3600.0
        assert job2.total_duration == 3700.0
        assert job2.filament_used == 15000.0
        # Original fields should remain
        assert job2.filename == "test.gcode"
        assert job2.start_time == start_time

    def test_upsert_print_job_with_metadata(self, db_session, sample_printer):
        """Test upsert with JSON metadata fields."""
        metadata = {"slicer": "OrcaSlicer", "version": "1.0.0"}
        auxiliary = {"custom_field": "custom_value"}

        job = upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="meta-job",
            filename="meta.gcode",
            status="completed",
            start_time=datetime.utcnow(),
            job_metadata=metadata,
            auxiliary_data=auxiliary
        )

        assert job.job_metadata == metadata
        assert job.auxiliary_data == auxiliary

    def test_get_jobs_by_printer(self, db_session, sample_printer):
        """Test getting all jobs for a printer."""
        # Create multiple jobs
        for i in range(3):
            upsert_print_job(
                db_session,
                printer_id=sample_printer.id,
                job_id=f"job-{i}",
                filename=f"file_{i}.gcode",
                status="completed" if i < 2 else "error",
                start_time=datetime.utcnow() - timedelta(hours=3 - i)
            )

        jobs = get_jobs_by_printer(db_session, sample_printer.id)

        assert len(jobs) == 3
        # Should be ordered by start_time descending (newest first)
        assert jobs[0].job_id == "job-2"
        assert jobs[1].job_id == "job-1"
        assert jobs[2].job_id == "job-0"

    def test_get_jobs_by_printer_with_status_filter(self, db_session, sample_printer):
        """Test getting jobs filtered by status."""
        # Create jobs with different statuses
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="completed-1",
            filename="c1.gcode",
            status="completed",
            start_time=datetime.utcnow()
        )
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="completed-2",
            filename="c2.gcode",
            status="completed",
            start_time=datetime.utcnow()
        )
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="error-1",
            filename="e1.gcode",
            status="error",
            start_time=datetime.utcnow()
        )

        completed_jobs = get_jobs_by_printer(db_session, sample_printer.id, status="completed")
        error_jobs = get_jobs_by_printer(db_session, sample_printer.id, status="error")

        assert len(completed_jobs) == 2
        assert len(error_jobs) == 1
        assert all(j.status == "completed" for j in completed_jobs)
        assert all(j.status == "error" for j in error_jobs)

    def test_get_jobs_by_printer_empty(self, db_session, sample_printer):
        """Test getting jobs for printer with no jobs."""
        jobs = get_jobs_by_printer(db_session, sample_printer.id)

        assert jobs == []


# ========== JobTotals CRUD Tests ==========

class TestJobTotalsCRUD:
    """Test JobTotals CRUD operations."""

    def test_update_job_totals_creates_record(self, db_session, sample_printer):
        """Test update_job_totals creates JobTotals if none exists."""
        # No jobs yet, but should create totals record
        totals = update_job_totals(db_session, sample_printer.id)

        assert totals is not None
        assert totals.printer_id == sample_printer.id
        assert totals.total_jobs == 0
        assert totals.total_time == 0.0
        assert totals.total_print_time == 0.0
        assert totals.total_filament_used == 0.0
        assert totals.longest_job == 0.0

    def test_update_job_totals_single_job(self, db_session, sample_printer):
        """Test job totals calculation with single completed job."""
        # Create a completed job
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="completed-job",
            filename="test.gcode",
            status="completed",
            start_time=datetime.utcnow(),
            print_duration=1800.0,  # 30 minutes
            total_duration=2000.0,  # 33+ minutes
            filament_used=5000.0    # 5 meters
        )

        totals = update_job_totals(db_session, sample_printer.id)

        assert totals.total_jobs == 1
        assert totals.total_time == 2000.0
        assert totals.total_print_time == 1800.0
        assert totals.total_filament_used == 5000.0
        assert totals.longest_job == 2000.0

    def test_update_job_totals_multiple_jobs(self, db_session, sample_printer):
        """Test job totals aggregation across multiple jobs."""
        # Create multiple completed jobs
        jobs_data = [
            {"job_id": "j1", "print_duration": 1000.0, "total_duration": 1100.0, "filament_used": 2000.0},
            {"job_id": "j2", "print_duration": 2000.0, "total_duration": 2200.0, "filament_used": 3000.0},
            {"job_id": "j3", "print_duration": 3000.0, "total_duration": 3300.0, "filament_used": 4000.0},
        ]

        for data in jobs_data:
            upsert_print_job(
                db_session,
                printer_id=sample_printer.id,
                filename="test.gcode",
                status="completed",
                start_time=datetime.utcnow(),
                **data
            )

        totals = update_job_totals(db_session, sample_printer.id)

        assert totals.total_jobs == 3
        assert totals.total_time == 1100.0 + 2200.0 + 3300.0  # 6600.0
        assert totals.total_print_time == 1000.0 + 2000.0 + 3000.0  # 6000.0
        assert totals.total_filament_used == 2000.0 + 3000.0 + 4000.0  # 9000.0
        assert totals.longest_job == 3300.0

    def test_update_job_totals_ignores_non_completed(self, db_session, sample_printer):
        """Test that only completed jobs are counted in totals."""
        # Create jobs with various statuses
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="completed",
            filename="c.gcode",
            status="completed",
            start_time=datetime.utcnow(),
            print_duration=1000.0,
            total_duration=1100.0,
            filament_used=2000.0
        )
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="error",
            filename="e.gcode",
            status="error",
            start_time=datetime.utcnow(),
            print_duration=500.0,
            total_duration=600.0,
            filament_used=1000.0
        )
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="cancelled",
            filename="x.gcode",
            status="cancelled",
            start_time=datetime.utcnow(),
            print_duration=300.0,
            total_duration=400.0,
            filament_used=500.0
        )

        totals = update_job_totals(db_session, sample_printer.id)

        # Only the completed job should be counted
        assert totals.total_jobs == 1
        assert totals.total_time == 1100.0
        assert totals.total_print_time == 1000.0
        assert totals.total_filament_used == 2000.0

    def test_update_job_totals_handles_null_values(self, db_session, sample_printer):
        """Test totals handle jobs with null duration/filament values."""
        # Create job with some null values
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="partial-data",
            filename="p.gcode",
            status="completed",
            start_time=datetime.utcnow(),
            print_duration=1000.0,
            total_duration=None,  # Null
            filament_used=None    # Null
        )

        totals = update_job_totals(db_session, sample_printer.id)

        assert totals.total_jobs == 1
        assert totals.total_print_time == 1000.0
        assert totals.total_time == 0.0  # Null treated as 0
        assert totals.total_filament_used == 0.0  # Null treated as 0

    def test_update_job_totals_updates_existing(self, db_session, sample_printer):
        """Test that existing JobTotals record is updated, not duplicated."""
        # Create initial totals
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="j1",
            filename="f1.gcode",
            status="completed",
            start_time=datetime.utcnow(),
            total_duration=1000.0,
            print_duration=900.0,
            filament_used=1000.0
        )
        totals1 = update_job_totals(db_session, sample_printer.id)
        totals1_id = totals1.id

        # Add another job and update totals
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="j2",
            filename="f2.gcode",
            status="completed",
            start_time=datetime.utcnow(),
            total_duration=2000.0,
            print_duration=1800.0,
            filament_used=2000.0
        )
        totals2 = update_job_totals(db_session, sample_printer.id)

        # Same record should be updated
        assert totals2.id == totals1_id
        assert totals2.total_jobs == 2
        assert totals2.total_time == 3000.0


# ========== JobDetails CRUD Tests ==========

class TestJobDetailsCRUD:
    """Test JobDetails CRUD operations."""

    def test_create_job_details(self, db_session, sample_print_job):
        """Test creating job details for a print job."""
        details = create_job_details(
            db_session,
            print_job_id=sample_print_job.id,
            layer_height=0.2,
            first_layer_height=0.3,
            nozzle_temp=210,
            bed_temp=60,
            filament_type="PLA"
        )

        assert details.id is not None
        assert details.print_job_id == sample_print_job.id
        assert details.layer_height == 0.2
        assert details.first_layer_height == 0.3
        assert details.nozzle_temp == 210
        assert details.bed_temp == 60
        assert details.filament_type == "PLA"

    def test_create_job_details_all_fields(self, db_session, sample_print_job):
        """Test creating job details with all optional fields."""
        raw_meta = {"custom": "data", "nested": {"value": 123}}

        details = create_job_details(
            db_session,
            print_job_id=sample_print_job.id,
            layer_height=0.2,
            first_layer_height=0.28,
            nozzle_temp=215,
            bed_temp=65,
            print_speed=60,
            infill_percentage=20,
            infill_pattern="gyroid",
            support_enabled=True,
            support_type="normal",
            filament_type="PETG",
            filament_brand="Overture",
            filament_color="Orange",
            estimated_time=7200,
            estimated_filament=25.5,
            layer_count=150,
            object_height=30.0,
            raw_metadata=raw_meta
        )

        assert details.print_speed == 60
        assert details.infill_percentage == 20
        assert details.infill_pattern == "gyroid"
        assert details.support_enabled is True
        assert details.support_type == "normal"
        assert details.filament_brand == "Overture"
        assert details.filament_color == "Orange"
        assert details.estimated_time == 7200
        assert details.estimated_filament == 25.5
        assert details.layer_count == 150
        assert details.object_height == 30.0
        assert details.raw_metadata == raw_meta

    def test_create_job_details_minimal(self, db_session, sample_print_job):
        """Test creating job details with minimal data."""
        details = create_job_details(
            db_session,
            print_job_id=sample_print_job.id
        )

        assert details.id is not None
        assert details.print_job_id == sample_print_job.id
        # All optional fields should be None
        assert details.layer_height is None
        assert details.filament_type is None


# ========== ApiKey CRUD Tests ==========

class TestApiKeyCRUD:
    """Test ApiKey CRUD operations."""

    def test_create_api_key(self, db_session):
        """Test creating a new API key."""
        api_key = create_api_key(
            db_session,
            key_hash="abc123def456abc123def456abc123def456abc123def456abc123def456abcd",
            key_prefix="3dp_abc1",
            name="Test API Key"
        )

        assert api_key.id is not None
        assert api_key.key_hash == "abc123def456abc123def456abc123def456abc123def456abc123def456abcd"
        assert api_key.key_prefix == "3dp_abc1"
        assert api_key.name == "Test API Key"
        assert api_key.is_active is True  # Default
        assert api_key.last_used is None
        assert api_key.expires_at is None

    def test_create_api_key_with_expiry(self, db_session):
        """Test creating an API key with expiration."""
        expiry = datetime.utcnow() + timedelta(days=30)

        api_key = create_api_key(
            db_session,
            key_hash="xyz789xyz789xyz789xyz789xyz789xyz789xyz789xyz789xyz789xyz789xyz7",
            key_prefix="3dp_xyz7",
            name="Expiring Key",
            expires_at=expiry,
            is_active=True
        )

        assert api_key.expires_at == expiry

    def test_get_api_key_by_hash_exists(self, db_session):
        """Test finding an API key by its hash."""
        key_hash = "findme123findme123findme123findme123findme123findme123findme12"

        create_api_key(
            db_session,
            key_hash=key_hash,
            key_prefix="3dp_find",
            name="Findable Key"
        )

        found = get_api_key_by_hash(db_session, key_hash)

        assert found is not None
        assert found.key_hash == key_hash
        assert found.name == "Findable Key"

    def test_get_api_key_by_hash_not_exists(self, db_session):
        """Test looking up non-existent API key returns None."""
        result = get_api_key_by_hash(
            db_session,
            "nonexistent123nonexistent123nonexistent123nonexistent123nonex12"
        )

        assert result is None

    def test_get_api_key_by_hash_inactive_key(self, db_session):
        """Test that inactive API keys are not returned."""
        key_hash = "inactive123inactive123inactive123inactive123inactive123inact12"

        create_api_key(
            db_session,
            key_hash=key_hash,
            key_prefix="3dp_inac",
            name="Inactive Key",
            is_active=False
        )

        result = get_api_key_by_hash(db_session, key_hash)

        assert result is None  # Inactive keys should not be returned

    def test_update_api_key_last_used(self, db_session):
        """Test updating API key last_used timestamp."""
        api_key = create_api_key(
            db_session,
            key_hash="updateme123updateme123updateme123updateme123updateme123updat12",
            key_prefix="3dp_updt",
            name="Usage Tracker"
        )

        # Initially last_used should be None
        assert api_key.last_used is None

        # Update last_used
        update_api_key_last_used(db_session, api_key.id)

        # Refresh to get updated value
        db_session.refresh(api_key)

        assert api_key.last_used is not None
        # Verify it's recent (within last minute)
        time_diff = datetime.utcnow() - api_key.last_used
        assert time_diff.total_seconds() < 60

    def test_update_api_key_last_used_multiple_times(self, db_session):
        """Test that last_used can be updated multiple times."""
        api_key = create_api_key(
            db_session,
            key_hash="multiuse123multiuse123multiuse123multiuse123multiuse123multi12",
            key_prefix="3dp_mult",
            name="Multi Use Key"
        )

        # First update
        update_api_key_last_used(db_session, api_key.id)
        db_session.refresh(api_key)
        first_use = api_key.last_used

        # Small delay and second update
        import time
        time.sleep(0.1)

        update_api_key_last_used(db_session, api_key.id)
        db_session.refresh(api_key)
        second_use = api_key.last_used

        # Second use should be after first use
        assert second_use >= first_use
