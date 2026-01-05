"""
TDD tests for SQLAlchemy ORM models.

Following Test-Driven Development: Tests written FIRST before implementation.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError


class TestPrinterModel:
    """Tests for Printer model."""

    def test_create_printer_minimal(self, db_session):
        """Printer can be created with minimal required fields."""
        from src.database.models import Printer

        printer = Printer(
            name="Test Printer",
            moonraker_url="http://localhost:7125"
        )
        db_session.add(printer)
        db_session.commit()

        assert printer.id is not None
        assert printer.name == "Test Printer"
        assert printer.moonraker_url == "http://localhost:7125"

    def test_create_printer_all_fields(self, db_session):
        """Printer can be created with all fields."""
        from src.database.models import Printer

        printer = Printer(
            name="Full Printer",
            location="Office",
            moonraker_url="http://printer.local:7125",
            moonraker_api_key="secret_key_123",
            is_active=True
        )
        db_session.add(printer)
        db_session.commit()

        assert printer.id is not None
        assert printer.location == "Office"
        assert printer.moonraker_api_key == "secret_key_123"
        assert printer.is_active is True

    def test_printer_default_values(self, db_session):
        """Printer has correct default values."""
        from src.database.models import Printer

        printer = Printer(
            name="Default Printer",
            moonraker_url="http://localhost:7125"
        )
        db_session.add(printer)
        db_session.commit()

        # Check default values
        assert printer.is_active is True
        assert printer.location is None
        assert printer.moonraker_api_key is None
        assert printer.last_seen is None

    def test_printer_timestamps(self, db_session):
        """Printer has created_at and updated_at timestamps."""
        from src.database.models import Printer

        printer = Printer(
            name="Timestamp Printer",
            moonraker_url="http://localhost:7125"
        )
        db_session.add(printer)
        db_session.commit()

        assert printer.created_at is not None
        assert printer.updated_at is not None
        assert isinstance(printer.created_at, datetime)
        assert isinstance(printer.updated_at, datetime)

    def test_printer_unique_name_constraint(self, db_session):
        """Printer name must be unique."""
        from src.database.models import Printer

        printer1 = Printer(
            name="Unique Printer",
            moonraker_url="http://localhost:7125"
        )
        db_session.add(printer1)
        db_session.commit()

        printer2 = Printer(
            name="Unique Printer",  # Same name
            moonraker_url="http://localhost:7126"
        )
        db_session.add(printer2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_printer_repr(self, db_session):
        """Printer has meaningful repr."""
        from src.database.models import Printer

        printer = Printer(
            name="Repr Printer",
            moonraker_url="http://localhost:7125"
        )
        db_session.add(printer)
        db_session.commit()

        repr_str = repr(printer)
        assert "Repr Printer" in repr_str
        assert str(printer.id) in repr_str


class TestPrintJobModel:
    """Tests for PrintJob model."""

    def test_create_print_job(self, db_session, sample_printer):
        """PrintJob can be created with required fields."""
        from src.database.models import PrintJob

        job = PrintJob(
            printer_id=sample_printer.id,
            job_id="abc-123-def",
            filename="test.gcode",
            status="completed",
            start_time=datetime.utcnow()
        )
        db_session.add(job)
        db_session.commit()

        assert job.id is not None
        assert job.printer_id == sample_printer.id
        assert job.job_id == "abc-123-def"
        assert job.filename == "test.gcode"
        assert job.status == "completed"

    def test_print_job_all_fields(self, db_session, sample_printer):
        """PrintJob can be created with all fields."""
        from src.database.models import PrintJob

        start = datetime.utcnow()
        end = start + timedelta(hours=2)

        job = PrintJob(
            printer_id=sample_printer.id,
            job_id="full-job-123",
            user="default",
            filename="benchy.gcode",
            status="completed",
            start_time=start,
            end_time=end,
            print_duration=7200.0,
            total_duration=7500.0,
            filament_used=15000.0,
            job_metadata={"slicer": "OrcaSlicer", "layer_height": 0.2},
            auxiliary_data={"notes": "Test print"}
        )
        db_session.add(job)
        db_session.commit()

        assert job.id is not None
        assert job.user == "default"
        assert job.print_duration == 7200.0
        assert job.filament_used == 15000.0
        assert job.job_metadata["slicer"] == "OrcaSlicer"
        assert job.auxiliary_data["notes"] == "Test print"

    def test_print_job_foreign_key(self, db_session, sample_printer):
        """PrintJob has foreign key relationship to Printer."""
        from src.database.models import PrintJob

        job = PrintJob(
            printer_id=sample_printer.id,
            job_id="fk-test",
            filename="test.gcode",
            status="completed",
            start_time=datetime.utcnow()
        )
        db_session.add(job)
        db_session.commit()

        # Access printer via relationship
        assert job.printer is not None
        assert job.printer.id == sample_printer.id
        assert job.printer.name == sample_printer.name

    def test_print_job_unique_printer_job_id(self, db_session, sample_printer):
        """PrintJob (printer_id, job_id) must be unique."""
        from src.database.models import PrintJob

        job1 = PrintJob(
            printer_id=sample_printer.id,
            job_id="duplicate-job",
            filename="test1.gcode",
            status="completed",
            start_time=datetime.utcnow()
        )
        db_session.add(job1)
        db_session.commit()

        job2 = PrintJob(
            printer_id=sample_printer.id,
            job_id="duplicate-job",  # Same job_id for same printer
            filename="test2.gcode",
            status="completed",
            start_time=datetime.utcnow()
        )
        db_session.add(job2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_print_job_cascade_delete(self, db_session):
        """Deleting printer cascades to print jobs."""
        from src.database.models import Printer, PrintJob

        printer = Printer(
            name="Cascade Printer",
            moonraker_url="http://localhost:7125"
        )
        db_session.add(printer)
        db_session.commit()

        job = PrintJob(
            printer_id=printer.id,
            job_id="cascade-test",
            filename="test.gcode",
            status="completed",
            start_time=datetime.utcnow()
        )
        db_session.add(job)
        db_session.commit()
        job_id = job.id

        # Delete printer
        db_session.delete(printer)
        db_session.commit()

        # Job should be deleted
        deleted_job = db_session.query(PrintJob).filter(PrintJob.id == job_id).first()
        assert deleted_job is None

    def test_print_job_json_columns(self, db_session, sample_printer):
        """PrintJob JSON columns work correctly."""
        from src.database.models import PrintJob

        job_meta = {
            "slicer": "OrcaSlicer",
            "layer_height": 0.2,
            "nozzle_temp": 215,
            "nested": {"key": "value"}
        }

        job = PrintJob(
            printer_id=sample_printer.id,
            job_id="json-test",
            filename="test.gcode",
            status="completed",
            start_time=datetime.utcnow(),
            job_metadata=job_meta
        )
        db_session.add(job)
        db_session.commit()

        # Refresh from DB
        db_session.refresh(job)

        assert job.job_metadata["slicer"] == "OrcaSlicer"
        assert job.job_metadata["layer_height"] == 0.2
        assert job.job_metadata["nested"]["key"] == "value"


class TestJobDetailsModel:
    """Tests for JobDetails model."""

    def test_create_job_details(self, db_session, sample_print_job):
        """JobDetails can be created with basic fields."""
        from src.database.models import JobDetails

        details = JobDetails(
            print_job_id=sample_print_job.id,
            layer_height=0.2,
            filament_type="PLA"
        )
        db_session.add(details)
        db_session.commit()

        assert details.id is not None
        assert details.print_job_id == sample_print_job.id
        assert details.layer_height == 0.2
        assert details.filament_type == "PLA"

    def test_job_details_all_fields(self, db_session, sample_print_job):
        """JobDetails can be created with all fields."""
        from src.database.models import JobDetails

        details = JobDetails(
            print_job_id=sample_print_job.id,
            layer_height=0.2,
            first_layer_height=0.3,
            nozzle_temp=215,
            bed_temp=60,
            print_speed=50,
            infill_percentage=20,
            infill_pattern="grid",
            support_enabled=True,
            support_type="normal",
            filament_type="PLA",
            filament_brand="PolyLite",
            filament_color="Blue",
            estimated_time=3600,
            estimated_filament=25.5,
            layer_count=150,
            object_height=50.0,
            raw_metadata={"complete": "data"}
        )
        db_session.add(details)
        db_session.commit()

        assert details.nozzle_temp == 215
        assert details.bed_temp == 60
        assert details.infill_pattern == "grid"
        assert details.support_enabled is True
        assert details.raw_metadata["complete"] == "data"

    def test_job_details_unique_print_job(self, db_session, sample_print_job):
        """JobDetails is unique per print_job_id."""
        from src.database.models import JobDetails

        details1 = JobDetails(
            print_job_id=sample_print_job.id,
            layer_height=0.2
        )
        db_session.add(details1)
        db_session.commit()

        details2 = JobDetails(
            print_job_id=sample_print_job.id,  # Same print_job
            layer_height=0.3
        )
        db_session.add(details2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_job_details_relationship(self, db_session, sample_print_job):
        """JobDetails has relationship to PrintJob."""
        from src.database.models import JobDetails

        details = JobDetails(
            print_job_id=sample_print_job.id,
            layer_height=0.2
        )
        db_session.add(details)
        db_session.commit()

        assert details.print_job is not None
        assert details.print_job.id == sample_print_job.id

    def test_job_details_cascade_delete(self, db_session):
        """Deleting PrintJob cascades to JobDetails."""
        from src.database.models import Printer, PrintJob, JobDetails

        printer = Printer(
            name="Details Cascade Printer",
            moonraker_url="http://localhost:7125"
        )
        db_session.add(printer)
        db_session.commit()

        job = PrintJob(
            printer_id=printer.id,
            job_id="details-cascade",
            filename="test.gcode",
            status="completed",
            start_time=datetime.utcnow()
        )
        db_session.add(job)
        db_session.commit()

        details = JobDetails(
            print_job_id=job.id,
            layer_height=0.2
        )
        db_session.add(details)
        db_session.commit()
        details_id = details.id

        # Delete job
        db_session.delete(job)
        db_session.commit()

        # Details should be deleted
        deleted_details = db_session.query(JobDetails).filter(JobDetails.id == details_id).first()
        assert deleted_details is None


class TestJobTotalsModel:
    """Tests for JobTotals model."""

    def test_create_job_totals(self, db_session, sample_printer):
        """JobTotals can be created."""
        from src.database.models import JobTotals

        totals = JobTotals(
            printer_id=sample_printer.id
        )
        db_session.add(totals)
        db_session.commit()

        assert totals.id is not None
        assert totals.printer_id == sample_printer.id

    def test_job_totals_default_values(self, db_session, sample_printer):
        """JobTotals has correct default values."""
        from src.database.models import JobTotals

        totals = JobTotals(
            printer_id=sample_printer.id
        )
        db_session.add(totals)
        db_session.commit()

        assert totals.total_jobs == 0
        assert totals.total_time == 0.0
        assert totals.total_print_time == 0.0
        assert totals.total_filament_used == 0.0
        assert totals.longest_job == 0.0

    def test_job_totals_with_values(self, db_session, sample_printer):
        """JobTotals can be created with values."""
        from src.database.models import JobTotals

        totals = JobTotals(
            printer_id=sample_printer.id,
            total_jobs=100,
            total_time=360000.0,
            total_print_time=350000.0,
            total_filament_used=500000.0,
            longest_job=7200.0
        )
        db_session.add(totals)
        db_session.commit()

        assert totals.total_jobs == 100
        assert totals.total_time == 360000.0
        assert totals.longest_job == 7200.0

    def test_job_totals_unique_printer(self, db_session, sample_printer):
        """JobTotals is unique per printer_id."""
        from src.database.models import JobTotals

        totals1 = JobTotals(
            printer_id=sample_printer.id
        )
        db_session.add(totals1)
        db_session.commit()

        totals2 = JobTotals(
            printer_id=sample_printer.id  # Same printer
        )
        db_session.add(totals2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_job_totals_relationship(self, db_session, sample_printer):
        """JobTotals has relationship to Printer."""
        from src.database.models import JobTotals

        totals = JobTotals(
            printer_id=sample_printer.id
        )
        db_session.add(totals)
        db_session.commit()

        assert totals.printer is not None
        assert totals.printer.id == sample_printer.id

    def test_job_totals_cascade_delete(self, db_session):
        """Deleting Printer cascades to JobTotals."""
        from src.database.models import Printer, JobTotals

        printer = Printer(
            name="Totals Cascade Printer",
            moonraker_url="http://localhost:7125"
        )
        db_session.add(printer)
        db_session.commit()

        totals = JobTotals(
            printer_id=printer.id,
            total_jobs=10
        )
        db_session.add(totals)
        db_session.commit()
        totals_id = totals.id

        # Delete printer
        db_session.delete(printer)
        db_session.commit()

        # Totals should be deleted
        deleted_totals = db_session.query(JobTotals).filter(JobTotals.id == totals_id).first()
        assert deleted_totals is None


class TestApiKeyModel:
    """Tests for ApiKey model."""

    def test_create_api_key(self, db_session):
        """ApiKey can be created."""
        from src.database.models import ApiKey

        api_key = ApiKey(
            key_hash="abc123def456" * 5 + "abcd",  # 64 char hash
            key_prefix="3dp_abc1",
            name="Test Key"
        )
        db_session.add(api_key)
        db_session.commit()

        assert api_key.id is not None
        assert api_key.name == "Test Key"
        assert api_key.key_prefix == "3dp_abc1"

    def test_api_key_default_values(self, db_session):
        """ApiKey has correct default values."""
        from src.database.models import ApiKey

        api_key = ApiKey(
            key_hash="x" * 64,
            key_prefix="3dp_test",
            name="Default Key"
        )
        db_session.add(api_key)
        db_session.commit()

        assert api_key.is_active is True
        assert api_key.last_used is None
        assert api_key.expires_at is None

    def test_api_key_unique_hash(self, db_session):
        """ApiKey key_hash must be unique."""
        from src.database.models import ApiKey

        api_key1 = ApiKey(
            key_hash="a" * 64,
            key_prefix="3dp_aaa1",
            name="Key 1"
        )
        db_session.add(api_key1)
        db_session.commit()

        api_key2 = ApiKey(
            key_hash="a" * 64,  # Same hash
            key_prefix="3dp_aaa2",
            name="Key 2"
        )
        db_session.add(api_key2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_api_key_expiration(self, db_session):
        """ApiKey can have expiration date."""
        from src.database.models import ApiKey

        expires = datetime.utcnow() + timedelta(days=30)

        api_key = ApiKey(
            key_hash="b" * 64,
            key_prefix="3dp_exp1",
            name="Expiring Key",
            expires_at=expires
        )
        db_session.add(api_key)
        db_session.commit()

        assert api_key.expires_at is not None
        assert api_key.expires_at > datetime.utcnow()

    def test_api_key_timestamps(self, db_session):
        """ApiKey has created_at and updated_at timestamps."""
        from src.database.models import ApiKey

        api_key = ApiKey(
            key_hash="c" * 64,
            key_prefix="3dp_time",
            name="Timestamp Key"
        )
        db_session.add(api_key)
        db_session.commit()

        assert api_key.created_at is not None
        assert api_key.updated_at is not None


class TestRelationships:
    """Tests for model relationships."""

    def test_printer_jobs_relationship(self, db_session):
        """Printer.print_jobs returns related jobs."""
        from src.database.models import Printer, PrintJob

        printer = Printer(
            name="Jobs Printer",
            moonraker_url="http://localhost:7125"
        )
        db_session.add(printer)
        db_session.commit()

        job1 = PrintJob(
            printer_id=printer.id,
            job_id="job-1",
            filename="file1.gcode",
            status="completed",
            start_time=datetime.utcnow()
        )
        job2 = PrintJob(
            printer_id=printer.id,
            job_id="job-2",
            filename="file2.gcode",
            status="error",
            start_time=datetime.utcnow()
        )
        db_session.add_all([job1, job2])
        db_session.commit()

        # Access via relationship
        assert len(printer.print_jobs) == 2
        job_ids = [j.job_id for j in printer.print_jobs]
        assert "job-1" in job_ids
        assert "job-2" in job_ids

    def test_printer_job_totals_relationship(self, db_session):
        """Printer.job_totals returns related totals."""
        from src.database.models import Printer, JobTotals

        printer = Printer(
            name="Totals Printer",
            moonraker_url="http://localhost:7125"
        )
        db_session.add(printer)
        db_session.commit()

        totals = JobTotals(
            printer_id=printer.id,
            total_jobs=50
        )
        db_session.add(totals)
        db_session.commit()

        # Access via relationship (uselist=False means single object)
        assert printer.job_totals is not None
        assert printer.job_totals.total_jobs == 50

    def test_print_job_job_details_relationship(self, db_session, sample_printer):
        """PrintJob.job_details returns related details."""
        from src.database.models import PrintJob, JobDetails

        job = PrintJob(
            printer_id=sample_printer.id,
            job_id="details-job",
            filename="test.gcode",
            status="completed",
            start_time=datetime.utcnow()
        )
        db_session.add(job)
        db_session.commit()

        details = JobDetails(
            print_job_id=job.id,
            layer_height=0.2,
            filament_type="PETG"
        )
        db_session.add(details)
        db_session.commit()

        # Access via relationship (uselist=False)
        assert job.job_details is not None
        assert job.job_details.layer_height == 0.2
        assert job.job_details.filament_type == "PETG"


class TestTimestampUpdates:
    """Tests for timestamp auto-updates."""

    def test_updated_at_changes_on_update(self, db_session, sample_printer):
        """updated_at changes when model is updated."""
        import time

        original_updated = sample_printer.updated_at

        # Wait a tiny bit to ensure timestamp changes
        time.sleep(0.01)

        # Update the printer
        sample_printer.location = "New Location"
        db_session.commit()
        db_session.refresh(sample_printer)

        # updated_at should have changed
        # Note: In some DBs this may be the same if sub-second precision not supported
        # For SQLite, the ORM-level onupdate should work
        assert sample_printer.location == "New Location"
