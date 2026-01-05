"""Tests for analytics endpoints."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status


class TestDashboardSummary:
    """Test GET /api/analytics/summary endpoint."""

    def test_summary_empty(self, client, auth_headers):
        """Summary when no jobs exist."""
        response = client.get("/api/analytics/summary", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_jobs"] == 0
        assert data["total_print_time"] == 0
        assert data["total_filament_used"] == 0
        assert data["successful_jobs"] == 0
        assert data["failed_jobs"] == 0

    def test_summary_with_jobs(
        self, client, auth_headers, db_session, sample_printer
    ):
        """Summary with existing jobs."""
        from src.database.models import PrintJob

        # Create completed job
        job1 = PrintJob(
            printer_id=sample_printer.id,
            job_id="job_1",
            filename="print1.gcode",
            status="completed",
            start_time=datetime.now(timezone.utc),
            print_duration=3600.0,  # 1 hour
            filament_used=10000.0,  # 10g
        )
        # Create failed job
        job2 = PrintJob(
            printer_id=sample_printer.id,
            job_id="job_2",
            filename="print2.gcode",
            status="error",
            start_time=datetime.now(timezone.utc),
            print_duration=1800.0,  # 30 min
            filament_used=5000.0,  # 5g
        )
        db_session.add_all([job1, job2])
        db_session.commit()

        response = client.get("/api/analytics/summary", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_jobs"] == 2
        assert data["total_print_time"] == 5400.0  # 1.5 hours
        assert data["total_filament_used"] == 15000.0  # 15g
        assert data["successful_jobs"] == 1
        assert data["failed_jobs"] == 1


class TestPrinterStats:
    """Test GET /api/analytics/printers endpoint."""

    def test_printer_stats_empty(self, client, auth_headers):
        """Printer stats when no printers exist."""
        response = client.get("/api/analytics/printers", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    def test_printer_stats_with_data(
        self, client, auth_headers, db_session, sample_printer
    ):
        """Printer stats with jobs."""
        from src.database.models import PrintJob

        job = PrintJob(
            printer_id=sample_printer.id,
            job_id="job_1",
            filename="test.gcode",
            status="completed",
            start_time=datetime.now(timezone.utc),
            print_duration=3600.0,
            filament_used=10000.0,
        )
        db_session.add(job)
        db_session.commit()

        response = client.get("/api/analytics/printers", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["printer_id"] == sample_printer.id
        assert data[0]["printer_name"] == "Test Printer"
        assert data[0]["total_jobs"] == 1
        assert data[0]["total_print_time"] == 3600.0


class TestFilamentUsage:
    """Test GET /api/analytics/filament endpoint."""

    def test_filament_usage_empty(self, client, auth_headers):
        """Filament usage when no jobs exist."""
        response = client.get("/api/analytics/filament", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    def test_filament_usage_by_type(
        self, client, auth_headers, db_session, sample_printer
    ):
        """Filament usage grouped by type."""
        from src.database.models import JobDetails, PrintJob

        # Create jobs with different filament types
        job1 = PrintJob(
            printer_id=sample_printer.id,
            job_id="job_1",
            filename="pla_print.gcode",
            status="completed",
            start_time=datetime.now(timezone.utc),
            filament_used=10000.0,
        )
        db_session.add(job1)
        db_session.flush()

        details1 = JobDetails(
            print_job_id=job1.id,
            filament_type="PLA",
        )
        db_session.add(details1)

        job2 = PrintJob(
            printer_id=sample_printer.id,
            job_id="job_2",
            filename="petg_print.gcode",
            status="completed",
            start_time=datetime.now(timezone.utc),
            filament_used=15000.0,
        )
        db_session.add(job2)
        db_session.flush()

        details2 = JobDetails(
            print_job_id=job2.id,
            filament_type="PETG",
        )
        db_session.add(details2)
        db_session.commit()

        response = client.get("/api/analytics/filament", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

        # Check that both filament types are represented
        filament_types = {item["filament_type"] for item in data}
        assert "PLA" in filament_types
        assert "PETG" in filament_types


class TestTimeline:
    """Test GET /api/analytics/timeline endpoint."""

    def test_timeline_empty(self, client, auth_headers):
        """Timeline when no jobs exist."""
        response = client.get("/api/analytics/timeline", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    def test_timeline_with_jobs(
        self, client, auth_headers, db_session, sample_printer
    ):
        """Timeline with jobs across multiple days."""
        from src.database.models import PrintJob

        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        # Create jobs on different days
        jobs = [
            PrintJob(
                printer_id=sample_printer.id,
                job_id=f"job_{i}",
                filename=f"print_{i}.gcode",
                status="completed",
                start_time=start_time,
                print_duration=3600.0,
            )
            for i, start_time in enumerate([now, now, yesterday, two_days_ago])
        ]
        db_session.add_all(jobs)
        db_session.commit()

        response = client.get("/api/analytics/timeline", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1  # At least one day with jobs

    def test_timeline_with_period(
        self, client, auth_headers, db_session, sample_printer
    ):
        """Timeline respects period parameter."""
        from src.database.models import PrintJob

        job = PrintJob(
            printer_id=sample_printer.id,
            job_id="job_1",
            filename="test.gcode",
            status="completed",
            start_time=datetime.now(timezone.utc),
            print_duration=3600.0,
        )
        db_session.add(job)
        db_session.commit()

        # Test daily period
        response = client.get(
            "/api/analytics/timeline?period=day", headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        # Test weekly period
        response = client.get(
            "/api/analytics/timeline?period=week", headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        # Test monthly period
        response = client.get(
            "/api/analytics/timeline?period=month", headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
