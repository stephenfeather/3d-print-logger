"""
Tests for Moonraker event handlers.

Tests follow TDD approach - written before implementation.
Covers job lifecycle tracking and database updates.
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, patch

from src.moonraker.handlers import (
    handle_status_update,
    handle_history_changed
)
from src.database.crud import (
    upsert_print_job,
    get_jobs_by_printer,
    update_job_totals
)


class TestStatusUpdateHandler:
    """Test handle_status_update event handler."""

    @pytest.mark.asyncio
    async def test_handle_printing_state_creates_job(self, db_session, sample_printer):
        """Test handle_status_update creates PrintJob when state is printing."""
        params = {
            "print_stats": {
                "state": "printing",
                "filename": "test_print.gcode",
                "print_duration": 0.0,
                "filament_used": 0.0,
                "message": ""
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        # Verify job was created
        jobs = get_jobs_by_printer(db_session, sample_printer.id, status="printing")
        assert len(jobs) > 0
        assert jobs[0].filename == "test_print.gcode"

    @pytest.mark.asyncio
    async def test_handle_paused_state_updates_job(self, db_session, sample_printer):
        """Test handle_status_update updates existing job when state is paused."""
        # Create initial job
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="test-job-123",
            filename="test_print.gcode",
            status="printing",
            start_time=datetime.now(UTC),
            print_duration=100.0,
            filament_used=50.0
        )

        params = {
            "print_stats": {
                "state": "paused",
                "filename": "test_print.gcode",
                "print_duration": 100.0,
                "filament_used": 50.0,
                "message": ""
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        # Verify job was updated
        jobs = get_jobs_by_printer(db_session, sample_printer.id)
        assert len(jobs) > 0
        assert jobs[0].status == "paused"

    @pytest.mark.asyncio
    async def test_handle_completed_state_finalizes_job(self, db_session, sample_printer):
        """Test handle_status_update finalizes job when state is complete."""
        start_time = datetime.now(UTC)
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="test-job-123",
            filename="test_print.gcode",
            status="printing",
            start_time=start_time,
            print_duration=1000.0,
            filament_used=500.0
        )

        params = {
            "print_stats": {
                "state": "complete",
                "filename": "test_print.gcode",
                "print_duration": 1000.0,
                "filament_used": 500.0,
                "message": ""
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        # Verify job was marked completed
        jobs = get_jobs_by_printer(db_session, sample_printer.id, status="completed")
        assert len(jobs) > 0
        assert jobs[0].status == "completed"
        assert jobs[0].end_time is not None

    @pytest.mark.asyncio
    async def test_handle_error_state_marks_job_failed(self, db_session, sample_printer):
        """Test handle_status_update marks job as error."""
        start_time = datetime.now(UTC)
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="test-job-456",
            filename="failing_print.gcode",
            status="printing",
            start_time=start_time,
            print_duration=500.0,
            filament_used=250.0
        )

        params = {
            "print_stats": {
                "state": "error",
                "filename": "failing_print.gcode",
                "print_duration": 500.0,
                "filament_used": 250.0,
                "message": "Nozzle crash detected"
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        # Verify job was marked error
        jobs = get_jobs_by_printer(db_session, sample_printer.id, status="error")
        assert len(jobs) > 0
        assert jobs[0].status == "error"

    @pytest.mark.asyncio
    async def test_handle_standby_cleans_up_stale_printing_jobs(self, db_session, sample_printer):
        """Test handle_status_update cleans up stale printing jobs when state is standby."""
        # Create a "stuck" printing job (simulating the bug scenario)
        stale_job = upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="active-old_print.gcode-" + str(sample_printer.id),
            filename="old_print.gcode",
            status="printing",
            start_time=datetime.now(UTC) - timedelta(hours=2),
            print_duration=1000.0,
            filament_used=500.0
        )

        params = {
            "print_stats": {
                "state": "standby",
                "filename": "",
                "print_duration": 0.0,
                "filament_used": 0.0,
                "message": ""
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        # Verify the stale printing job was marked as cancelled
        db_session.refresh(stale_job)
        assert stale_job.status == "cancelled"
        assert stale_job.end_time is not None

    @pytest.mark.asyncio
    async def test_handle_standby_does_not_create_new_job(self, db_session, sample_printer):
        """Test handle_status_update does not create new job when state is standby."""
        params = {
            "print_stats": {
                "state": "standby",
                "filename": "",
                "print_duration": 0.0,
                "filament_used": 0.0,
                "message": ""
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        # Verify no job was created
        jobs = get_jobs_by_printer(db_session, sample_printer.id)
        assert len(jobs) == 0

    @pytest.mark.asyncio
    async def test_handle_completion_cleans_up_other_stale_jobs(self, db_session, sample_printer):
        """Test handle_status_update cleans up other stale printing jobs when a job completes."""
        # Create a stale "printing" job for a DIFFERENT file
        stale_job = upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id=f"active-old_file.gcode-{sample_printer.id}",
            filename="old_file.gcode",
            status="printing",
            start_time=datetime.now(UTC) - timedelta(hours=2),
            print_duration=1000.0,
            filament_used=500.0
        )

        # Now complete a different print
        params = {
            "print_stats": {
                "state": "complete",
                "filename": "new_file.gcode",  # Different filename!
                "print_duration": 2000.0,
                "filament_used": 1000.0,
                "message": ""
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        # Verify the stale job was marked as cancelled
        db_session.refresh(stale_job)
        assert stale_job.status == "cancelled"
        assert stale_job.end_time is not None

    @pytest.mark.asyncio
    async def test_handle_completion_updates_job_totals(self, db_session, sample_printer):
        """Test handle_status_update updates JobTotals when job completes."""
        # Create and complete a job
        start_time = datetime.now(UTC)
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="test-job-789",
            filename="test_print.gcode",
            status="printing",
            start_time=start_time,
            print_duration=1000.0,
            total_duration=1200.0,
            filament_used=500.0
        )

        params = {
            "print_stats": {
                "state": "complete",
                "filename": "test_print.gcode",
                "print_duration": 1000.0,
                "filament_used": 500.0,
                "message": ""
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        # Verify totals were updated
        totals = update_job_totals(db_session, sample_printer.id)
        assert totals.total_jobs == 1
        assert totals.total_filament_used == 500.0

    @pytest.mark.asyncio
    async def test_handle_missing_print_stats_is_safe(self, db_session, sample_printer):
        """Test handle_status_update safely handles missing print_stats."""
        params = {}

        # Should not raise exception
        await handle_status_update(sample_printer.id, params, db_session)

    @pytest.mark.asyncio
    async def test_handle_extracts_print_stats_correctly(self, db_session, sample_printer):
        """Test handle_status_update extracts print_stats fields correctly."""
        params = {
            "print_stats": {
                "state": "printing",
                "filename": "multipart_print.gcode",
                "print_duration": 123.45,
                "filament_used": 678.90,
                "message": "Layer 5"
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        jobs = get_jobs_by_printer(db_session, sample_printer.id)
        assert len(jobs) > 0
        assert jobs[0].filename == "multipart_print.gcode"
        assert abs(jobs[0].print_duration - 123.45) < 0.01


class TestHistoryChangedHandler:
    """Test handle_history_changed event handler."""

    @pytest.mark.asyncio
    async def test_handle_history_finished_action(self, db_session, sample_printer):
        """Test handle_history_changed processes finished action."""
        job_data = {
            "job_id": "history-job-123",
            "filename": "historical_print.gcode",
            "start_time": datetime.now(UTC).timestamp(),
            "end_time": (datetime.now(UTC) + timedelta(hours=2)).timestamp(),
            "print_duration": 7200,
            "filament_used": 1000.0,
            "status": "completed"
        }

        params = {
            "action": "finished",
            "job": job_data
        }

        await handle_history_changed(sample_printer.id, params, db_session)

        # Verify job was synced from history
        jobs = get_jobs_by_printer(db_session, sample_printer.id)
        assert len(jobs) > 0

    @pytest.mark.asyncio
    async def test_handle_history_added_action(self, db_session, sample_printer):
        """Test handle_history_changed processes added action."""
        job_data = {
            "job_id": "new-history-job",
            "filename": "new_print.gcode",
            "start_time": datetime.now(UTC).timestamp(),
            "end_time": None,
            "print_duration": 0,
            "filament_used": 0,
            "status": "printing"
        }

        params = {
            "action": "added",
            "job": job_data
        }

        await handle_history_changed(sample_printer.id, params, db_session)

        # Should handle added action without error

    @pytest.mark.asyncio
    async def test_handle_history_deleted_action(self, db_session, sample_printer):
        """Test handle_history_changed handles deleted action."""
        # Create a job first
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="deleted-job-123",
            filename="deleted_print.gcode",
            status="completed",
            start_time=datetime.now(UTC),
            print_duration=1000.0,
            filament_used=500.0
        )

        params = {
            "action": "deleted",
            "job": {
                "job_id": "deleted-job-123",
                "filename": "deleted_print.gcode"
            }
        }

        # Should handle deleted action without error
        await handle_history_changed(sample_printer.id, params, db_session)

    @pytest.mark.asyncio
    async def test_handle_history_handles_missing_action(self, db_session, sample_printer):
        """Test handle_history_changed safely handles missing action."""
        params = {"job": {}}

        # Should not raise exception
        await handle_history_changed(sample_printer.id, params, db_session)

    @pytest.mark.asyncio
    async def test_handle_history_handles_missing_job(self, db_session, sample_printer):
        """Test handle_history_changed safely handles missing job data."""
        params = {"action": "finished"}

        # Should not raise exception
        await handle_history_changed(sample_printer.id, params, db_session)

    @pytest.mark.asyncio
    async def test_handle_history_syncs_job_with_all_fields(self, db_session, sample_printer):
        """Test handle_history_changed correctly syncs all job fields."""
        start_timestamp = datetime.now(UTC).timestamp()
        end_timestamp = (datetime.now(UTC) + timedelta(hours=3)).timestamp()

        job_data = {
            "job_id": "complete-history-job",
            "filename": "complete_print.gcode",
            "start_time": start_timestamp,
            "end_time": end_timestamp,
            "print_duration": 10000,
            "total_duration": 10800,
            "filament_used": 1500.0,
            "status": "completed",
            "user": "default"
        }

        params = {
            "action": "finished",
            "job": job_data
        }

        await handle_history_changed(sample_printer.id, params, db_session)

        jobs = get_jobs_by_printer(db_session, sample_printer.id)
        assert len(jobs) > 0
        assert jobs[0].job_id == "complete-history-job"
        assert jobs[0].filename == "complete_print.gcode"

    @pytest.mark.asyncio
    async def test_handle_history_updates_printer_last_seen(self, db_session, sample_printer):
        """Test handle_history_changed updates printer's last_seen timestamp."""
        from src.database.crud import get_printer

        # Verify printer initially has no last_seen
        printer = get_printer(db_session, sample_printer.id)
        assert printer.last_seen is None

        # Send history event
        job_data = {
            "job_id": "test-job-789",
            "filename": "test.gcode",
            "start_time": datetime.now(UTC).timestamp(),
            "end_time": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
            "print_duration": 3600,
            "filament_used": 500.0,
            "status": "completed"
        }

        params = {
            "action": "finished",
            "job": job_data
        }

        await handle_history_changed(sample_printer.id, params, db_session)

        # Verify last_seen was updated
        db_session.refresh(printer)
        assert printer.last_seen is not None
        assert (datetime.now(UTC) - printer.last_seen).total_seconds() < 5

    @pytest.mark.asyncio
    async def test_handle_history_changed_with_list_params(self, db_session, sample_printer):
        """Test handle_history_changed handles list format params from Moonraker.

        Moonraker sends history notifications as [{"action": ..., "job": ...}]
        not as a flat dict. This test verifies we handle both formats.
        """
        job_data = {
            "job_id": "list-format-job-123",
            "filename": "list_format_test.gcode",
            "start_time": datetime.now(UTC).timestamp(),
            "end_time": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
            "print_duration": 3600,
            "filament_used": 500.0,
            "status": "completed"
        }

        # Moonraker sends params as a list containing the data dict
        params = [{"action": "finished", "job": job_data}]

        await handle_history_changed(sample_printer.id, params, db_session)

        # Verify job was synced from history
        jobs = get_jobs_by_printer(db_session, sample_printer.id)
        assert len(jobs) > 0
        assert jobs[0].job_id == "list-format-job-123"
        assert jobs[0].filename == "list_format_test.gcode"
        assert jobs[0].status == "completed"

    @pytest.mark.asyncio
    async def test_handle_history_finished_cleans_up_synthetic_jobs(self, db_session, sample_printer):
        """Test handle_history_changed cleans up synthetic job when real job finishes."""
        # Create a synthetic "printing" job (what status_update creates)
        synthetic_job = upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id=f"active-test_print.gcode-{sample_printer.id}",
            filename="test_print.gcode",
            status="printing",
            start_time=datetime.now(UTC) - timedelta(hours=1),
            print_duration=500.0,
            filament_used=250.0
        )

        # Now receive the history "finished" event with the real Moonraker job ID
        job_data = {
            "job_id": "000001234-abcd-efgh",  # Real Moonraker UUID
            "filename": "test_print.gcode",  # Same filename
            "start_time": (datetime.now(UTC) - timedelta(hours=1)).timestamp(),
            "end_time": datetime.now(UTC).timestamp(),
            "print_duration": 3600,
            "filament_used": 500.0,
            "status": "completed"
        }

        params = {
            "action": "finished",
            "job": job_data
        }

        await handle_history_changed(sample_printer.id, params, db_session)

        # Verify the synthetic printing job was marked as completed
        db_session.refresh(synthetic_job)
        assert synthetic_job.status == "completed"
        assert synthetic_job.end_time is not None


class TestHandlerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_handlers_with_none_values(self, db_session, sample_printer):
        """Test handlers safely handle None values."""
        params = {
            "print_stats": {
                "state": "printing",
                "filename": None,
                "print_duration": None,
                "filament_used": None,
                "message": None
            }
        }

        # Should not raise exception
        await handle_status_update(sample_printer.id, params, db_session)

    @pytest.mark.asyncio
    async def test_handlers_with_empty_dicts(self, db_session, sample_printer):
        """Test handlers safely handle empty dictionaries."""
        params = {
            "print_stats": {}
        }

        # Should not raise exception
        await handle_status_update(sample_printer.id, params, db_session)

    @pytest.mark.asyncio
    async def test_handler_preserves_existing_data(self, db_session, sample_printer):
        """Test handler doesn't overwrite important data during updates."""
        start_time = datetime.now(UTC)
        upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="preserve-job",
            filename="preserve.gcode",
            status="printing",
            start_time=start_time,
            print_duration=100.0,
            filament_used=50.0,
            user="test_user"
        )

        params = {
            "print_stats": {
                "state": "paused",
                "filename": "preserve.gcode",
                "print_duration": 150.0,
                "filament_used": 75.0
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        jobs = get_jobs_by_printer(db_session, sample_printer.id)
        # User data should be preserved
        assert jobs[0].user == "test_user"

    @pytest.mark.asyncio
    async def test_metric_updates_without_state_change(self, db_session, sample_printer):
        """Test status updates with only metrics (no state) update active job."""
        # Create an active printing job
        initial_job = upsert_print_job(
            db_session,
            printer_id=sample_printer.id,
            job_id="active-metrics-test.gcode-1",
            filename="metrics-test.gcode",
            status="printing",
            start_time=datetime.now(UTC),
            print_duration=100.0,
            filament_used=50.0
        )

        # Status update with only metrics (no state) - this is what Moonraker sends
        # during active printing
        params = {
            "print_stats": {
                "print_duration": 500.0,
                "filament_used": 200.0
                # No "state" field - this is the key point!
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        # Verify metrics were updated
        db_session.refresh(initial_job)
        assert initial_job.print_duration == 500.0
        assert initial_job.filament_used == 200.0

    @pytest.mark.asyncio
    async def test_datetimes_are_timezone_aware_utc(self, db_session, sample_printer):
        """Test that all datetimes created by handlers are timezone-aware in UTC."""
        params = {
            "print_stats": {
                "state": "printing",
                "filename": "tz_test.gcode",
                "print_duration": 0.0,
                "filament_used": 0.0,
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        jobs = get_jobs_by_printer(db_session, sample_printer.id)
        assert len(jobs) > 0

        job = jobs[0]
        # Verify start_time is timezone-aware UTC
        assert job.start_time is not None
        assert job.start_time.tzinfo is not None
        assert job.start_time.tzinfo == UTC

        # Update to completion
        params = {
            "print_stats": {
                "state": "complete",
                "filename": "tz_test.gcode",
                "print_duration": 100.0,
                "filament_used": 50.0,
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        db_session.refresh(job)
        # Verify end_time is also timezone-aware UTC
        assert job.end_time is not None
        assert job.end_time.tzinfo is not None
        assert job.end_time.tzinfo == UTC

    @pytest.mark.asyncio
    async def test_cancelled_job_not_overwritten_on_reprint(self, db_session, sample_printer):
        """Test that reprinting a file after cancellation creates a new job.

        This tests issue #17: Synthetic job IDs can overwrite cancelled/failed job records on reprint
        https://github.com/user/repo/issues/17

        Bug scenario:
        1. Start printing benchy.gcode → creates synthetic job "active-benchy.gcode-1"
        2. Cancel print → job updated to "cancelled"
        3. Reprint benchy.gcode → should create NEW record, but was overwriting cancelled one
        """
        # Step 1: Start printing benchy.gcode
        params = {
            "print_stats": {
                "state": "printing",
                "filename": "benchy.gcode",
                "print_duration": 0.0,
                "filament_used": 0.0,
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        jobs = get_jobs_by_printer(db_session, sample_printer.id)
        assert len(jobs) == 1
        first_job = jobs[0]
        assert first_job.status == "printing"
        assert first_job.filename == "benchy.gcode"

        # Step 2: Cancel the print (transition to standby)
        params = {
            "print_stats": {
                "state": "standby",
                "filename": "",
                "print_duration": 100.0,
                "filament_used": 50.0,
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        db_session.refresh(first_job)
        assert first_job.status == "cancelled"

        # Step 3: Reprint the same file
        params = {
            "print_stats": {
                "state": "printing",
                "filename": "benchy.gcode",
                "print_duration": 0.0,
                "filament_used": 0.0,
            }
        }

        await handle_status_update(sample_printer.id, params, db_session)

        # Verify we have TWO jobs now, not one
        jobs = get_jobs_by_printer(db_session, sample_printer.id)
        assert len(jobs) == 2, f"Should have 2 jobs (original cancelled + new printing), got {len(jobs)}"

        # Verify the first job is still cancelled
        assert first_job.status == "cancelled"

        # Verify the second job is printing
        new_job = next(j for j in jobs if j.id != first_job.id)
        assert new_job.status == "printing"
        assert new_job.filename == "benchy.gcode"
