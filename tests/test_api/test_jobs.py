"""Tests for job endpoints."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status


class TestListJobs:
    """Test GET /api/jobs endpoint."""

    def test_list_jobs_empty(self, client, auth_headers):
        """List jobs when none exist."""
        response = client.get("/api/jobs", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["has_more"] is False

    def test_list_jobs_with_data(self, client, auth_headers, sample_job):
        """List jobs with existing data."""
        response = client.get("/api/jobs", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["filename"] == "test_print.gcode"
        assert data["total"] == 1

    def test_list_jobs_pagination(self, client, auth_headers, db_session, sample_printer):
        """Jobs should support pagination."""
        from src.database.models import PrintJob

        # Create 5 jobs
        for i in range(5):
            job = PrintJob(
                printer_id=sample_printer.id,
                job_id=f"job_{i}",
                filename=f"print_{i}.gcode",
                status="completed",
                start_time=datetime.now(timezone.utc),
            )
            db_session.add(job)
        db_session.commit()

        # Get first page (limit 2)
        response = client.get("/api/jobs?limit=2&offset=0", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert data["has_more"] is True

        # Get second page
        response = client.get("/api/jobs?limit=2&offset=2", headers=auth_headers)
        data = response.json()
        assert len(data["items"]) == 2
        assert data["offset"] == 2
        assert data["has_more"] is True

        # Get last page
        response = client.get("/api/jobs?limit=2&offset=4", headers=auth_headers)
        data = response.json()
        assert len(data["items"]) == 1
        assert data["has_more"] is False

    def test_list_jobs_filter_by_printer(
        self, client, auth_headers, db_session, sample_printer
    ):
        """Filter jobs by printer_id."""
        from src.database.models import Printer, PrintJob

        # Create second printer with jobs
        printer2 = Printer(
            name="Second Printer",
            moonraker_url="http://second:7125",
            is_active=True,
        )
        db_session.add(printer2)
        db_session.commit()

        # Jobs for first printer
        job1 = PrintJob(
            printer_id=sample_printer.id,
            job_id="job_1",
            filename="first_printer.gcode",
            status="completed",
            start_time=datetime.now(timezone.utc),
        )
        # Jobs for second printer
        job2 = PrintJob(
            printer_id=printer2.id,
            job_id="job_2",
            filename="second_printer.gcode",
            status="completed",
            start_time=datetime.now(timezone.utc),
        )
        db_session.add_all([job1, job2])
        db_session.commit()

        # Filter by first printer
        response = client.get(
            f"/api/jobs?printer_id={sample_printer.id}", headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["filename"] == "first_printer.gcode"

    def test_list_jobs_filter_by_status(
        self, client, auth_headers, db_session, sample_printer
    ):
        """Filter jobs by status."""
        from src.database.models import PrintJob

        # Create jobs with different statuses
        completed = PrintJob(
            printer_id=sample_printer.id,
            job_id="completed_job",
            filename="completed.gcode",
            status="completed",
            start_time=datetime.now(timezone.utc),
        )
        failed = PrintJob(
            printer_id=sample_printer.id,
            job_id="failed_job",
            filename="failed.gcode",
            status="error",
            start_time=datetime.now(timezone.utc),
        )
        db_session.add_all([completed, failed])
        db_session.commit()

        # Filter completed only
        response = client.get("/api/jobs?status=completed", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "completed"

    def test_list_jobs_filter_by_date_range(
        self, client, auth_headers, db_session, sample_printer
    ):
        """Filter jobs by date range."""
        from src.database.models import PrintJob

        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        last_week = now - timedelta(days=7)

        # Create jobs with different start times
        recent = PrintJob(
            printer_id=sample_printer.id,
            job_id="recent_job",
            filename="recent.gcode",
            status="completed",
            start_time=yesterday,
        )
        old = PrintJob(
            printer_id=sample_printer.id,
            job_id="old_job",
            filename="old.gcode",
            status="completed",
            start_time=last_week,
        )
        db_session.add_all([recent, old])
        db_session.commit()

        # Filter by start_after (2 days ago)
        # Use Z suffix for UTC timezone (URL-safe)
        two_days_ago = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        response = client.get(
            f"/api/jobs?start_after={two_days_ago}", headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["filename"] == "recent.gcode"


class TestGetJob:
    """Test GET /api/jobs/{job_id} endpoint."""

    def test_get_job_success(self, client, auth_headers, sample_job):
        """Get existing job."""
        response = client.get(f"/api/jobs/{sample_job.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_job.id
        assert data["filename"] == "test_print.gcode"

    def test_get_job_not_found(self, client, auth_headers):
        """Non-existent job should return 404."""
        response = client.get("/api/jobs/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_job_with_details(self, client, auth_headers, db_session, sample_job):
        """Job response should include details if available."""
        from src.database.models import JobDetails

        details = JobDetails(
            print_job_id=sample_job.id,
            layer_height=0.2,
            nozzle_temp=210,
            bed_temp=60,
            infill_percentage=20,
            filament_type="PLA",
        )
        db_session.add(details)
        db_session.commit()

        response = client.get(f"/api/jobs/{sample_job.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["details"] is not None
        assert data["details"]["layer_height"] == 0.2
        assert data["details"]["filament_type"] == "PLA"


class TestDeleteJob:
    """Test DELETE /api/jobs/{job_id} endpoint."""

    def test_delete_job_success(self, client, auth_headers, sample_job):
        """Delete existing job."""
        response = client.delete(f"/api/jobs/{sample_job.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        response = client.get(f"/api/jobs/{sample_job.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_job_not_found(self, client, auth_headers):
        """Delete non-existent job should return 404."""
        response = client.delete("/api/jobs/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestJobsByPrinter:
    """Test GET /api/printers/{printer_id}/jobs endpoint."""

    def test_get_printer_jobs(self, client, auth_headers, sample_job, sample_printer):
        """Get jobs for a specific printer."""
        response = client.get(
            f"/api/printers/{sample_printer.id}/jobs", headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["printer_id"] == sample_printer.id

    def test_get_printer_jobs_not_found(self, client, auth_headers):
        """Jobs for non-existent printer should return 404."""
        response = client.get("/api/printers/99999/jobs", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
