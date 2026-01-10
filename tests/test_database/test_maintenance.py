"""
TDD tests for MaintenanceRecord model and CRUD operations.

Issue #9: Minimal Printer Maintenance Details

Following Test-Driven Development: Tests written FIRST before implementation.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError


class TestMaintenanceRecordModel:
    """Tests for MaintenanceRecord model."""

    def test_create_maintenance_record_minimal(self, db_session, sample_printer):
        """MaintenanceRecord can be created with minimal required fields."""
        from src.database.models import MaintenanceRecord

        record = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="cleaning",
            description="Cleaned nozzle and bed"
        )
        db_session.add(record)
        db_session.commit()

        assert record.id is not None
        assert record.printer_id == sample_printer.id
        assert record.category == "cleaning"
        assert record.description == "Cleaned nozzle and bed"

    def test_create_maintenance_record_all_fields(self, db_session, sample_printer):
        """MaintenanceRecord can be created with all fields."""
        from src.database.models import MaintenanceRecord

        maintenance_date = datetime.utcnow()

        record = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=maintenance_date,
            done=True,
            category="parts_replacement",
            description="Replaced hotend",
            cost=45.99,
            notes="Used E3D V6 hotend, installed new thermistor"
        )
        db_session.add(record)
        db_session.commit()

        assert record.id is not None
        assert record.done is True
        assert record.cost == 45.99
        assert record.notes == "Used E3D V6 hotend, installed new thermistor"

    def test_maintenance_record_default_values(self, db_session, sample_printer):
        """MaintenanceRecord has correct default values."""
        from src.database.models import MaintenanceRecord

        record = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="inspection",
            description="Monthly inspection"
        )
        db_session.add(record)
        db_session.commit()

        # Check default values
        assert record.done is False
        assert record.cost is None
        assert record.notes is None

    def test_maintenance_record_timestamps(self, db_session, sample_printer):
        """MaintenanceRecord has created_at and updated_at timestamps."""
        from src.database.models import MaintenanceRecord

        record = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="calibration",
            description="Bed leveling"
        )
        db_session.add(record)
        db_session.commit()

        assert record.created_at is not None
        assert record.updated_at is not None
        assert isinstance(record.created_at, datetime)
        assert isinstance(record.updated_at, datetime)

    def test_maintenance_record_foreign_key(self, db_session, sample_printer):
        """MaintenanceRecord has foreign key relationship to Printer."""
        from src.database.models import MaintenanceRecord

        record = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="repair",
            description="Fixed extruder gear"
        )
        db_session.add(record)
        db_session.commit()

        # Access printer via relationship
        assert record.printer is not None
        assert record.printer.id == sample_printer.id
        assert record.printer.name == sample_printer.name

    def test_maintenance_record_cascade_delete(self, db_session):
        """Deleting printer cascades to maintenance records."""
        from src.database.models import Printer, MaintenanceRecord

        printer = Printer(
            name="Cascade Maintenance Printer",
            moonraker_url="http://localhost:7125"
        )
        db_session.add(printer)
        db_session.commit()

        record = MaintenanceRecord(
            printer_id=printer.id,
            date=datetime.utcnow(),
            category="cleaning",
            description="Test cleaning"
        )
        db_session.add(record)
        db_session.commit()
        record_id = record.id

        # Delete printer
        db_session.delete(printer)
        db_session.commit()

        # Record should be deleted
        deleted_record = db_session.query(MaintenanceRecord).filter(
            MaintenanceRecord.id == record_id
        ).first()
        assert deleted_record is None

    def test_maintenance_record_repr(self, db_session, sample_printer):
        """MaintenanceRecord has meaningful repr."""
        from src.database.models import MaintenanceRecord

        record = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="calibration",
            description="Test repr"
        )
        db_session.add(record)
        db_session.commit()

        repr_str = repr(record)
        assert "MaintenanceRecord" in repr_str
        assert str(record.id) in repr_str
        assert "calibration" in repr_str

    def test_printer_maintenance_records_relationship(self, db_session, sample_printer):
        """Printer.maintenance_records returns related records."""
        from src.database.models import MaintenanceRecord

        record1 = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="cleaning",
            description="Cleaning 1"
        )
        record2 = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="calibration",
            description="Calibration 1"
        )
        db_session.add_all([record1, record2])
        db_session.commit()

        # Access via relationship
        assert len(sample_printer.maintenance_records) == 2
        categories = [r.category for r in sample_printer.maintenance_records]
        assert "cleaning" in categories
        assert "calibration" in categories


class TestMaintenanceRecordCRUD:
    """Tests for MaintenanceRecord CRUD operations."""

    def test_create_maintenance_record(self, db_session, sample_printer):
        """create_maintenance_record creates a record."""
        from src.database.crud import create_maintenance_record

        record = create_maintenance_record(
            db_session,
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="cleaning",
            description="Nozzle cleaning"
        )

        assert record.id is not None
        assert record.printer_id == sample_printer.id
        assert record.category == "cleaning"
        assert record.description == "Nozzle cleaning"

    def test_create_maintenance_record_with_optional_fields(self, db_session, sample_printer):
        """create_maintenance_record accepts optional fields."""
        from src.database.crud import create_maintenance_record

        record = create_maintenance_record(
            db_session,
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="parts_replacement",
            description="New nozzle",
            done=True,
            cost=5.99,
            notes="0.4mm brass nozzle"
        )

        assert record.done is True
        assert record.cost == 5.99
        assert record.notes == "0.4mm brass nozzle"

    def test_get_maintenance_record(self, db_session, sample_printer):
        """get_maintenance_record retrieves a record by ID."""
        from src.database.crud import create_maintenance_record, get_maintenance_record

        created = create_maintenance_record(
            db_session,
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="inspection",
            description="Weekly check"
        )

        record = get_maintenance_record(db_session, created.id)

        assert record is not None
        assert record.id == created.id
        assert record.category == "inspection"

    def test_get_maintenance_record_not_found(self, db_session):
        """get_maintenance_record returns None for nonexistent ID."""
        from src.database.crud import get_maintenance_record

        record = get_maintenance_record(db_session, 99999)

        assert record is None

    def test_get_maintenance_records_all(self, db_session, sample_printer):
        """get_maintenance_records returns all records."""
        from src.database.crud import create_maintenance_record, get_maintenance_records

        create_maintenance_record(
            db_session,
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="cleaning",
            description="Cleaning 1"
        )
        create_maintenance_record(
            db_session,
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="calibration",
            description="Calibration 1"
        )

        records = get_maintenance_records(db_session)

        assert len(records) == 2

    def test_get_maintenance_records_by_printer(self, db_session):
        """get_maintenance_records filters by printer_id."""
        from src.database.models import Printer
        from src.database.crud import create_maintenance_record, get_maintenance_records

        printer1 = Printer(name="Printer 1", moonraker_url="http://p1:7125")
        printer2 = Printer(name="Printer 2", moonraker_url="http://p2:7125")
        db_session.add_all([printer1, printer2])
        db_session.commit()

        create_maintenance_record(
            db_session,
            printer_id=printer1.id,
            date=datetime.utcnow(),
            category="cleaning",
            description="P1 cleaning"
        )
        create_maintenance_record(
            db_session,
            printer_id=printer2.id,
            date=datetime.utcnow(),
            category="calibration",
            description="P2 calibration"
        )

        records = get_maintenance_records(db_session, printer_id=printer1.id)

        assert len(records) == 1
        assert records[0].description == "P1 cleaning"

    def test_get_maintenance_records_by_done_status(self, db_session, sample_printer):
        """get_maintenance_records filters by done status."""
        from src.database.crud import create_maintenance_record, get_maintenance_records

        create_maintenance_record(
            db_session,
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="cleaning",
            description="Done cleaning",
            done=True
        )
        create_maintenance_record(
            db_session,
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="calibration",
            description="Pending calibration",
            done=False
        )

        done_records = get_maintenance_records(db_session, done=True)
        pending_records = get_maintenance_records(db_session, done=False)

        assert len(done_records) == 1
        assert done_records[0].description == "Done cleaning"
        assert len(pending_records) == 1
        assert pending_records[0].description == "Pending calibration"

    def test_get_maintenance_records_ordered_by_date(self, db_session, sample_printer):
        """get_maintenance_records returns records ordered by date descending."""
        from src.database.crud import create_maintenance_record, get_maintenance_records

        old_date = datetime.utcnow() - timedelta(days=7)
        new_date = datetime.utcnow()

        create_maintenance_record(
            db_session,
            printer_id=sample_printer.id,
            date=old_date,
            category="old",
            description="Old record"
        )
        create_maintenance_record(
            db_session,
            printer_id=sample_printer.id,
            date=new_date,
            category="new",
            description="New record"
        )

        records = get_maintenance_records(db_session)

        assert len(records) == 2
        assert records[0].category == "new"  # Most recent first
        assert records[1].category == "old"

    def test_update_maintenance_record(self, db_session, sample_printer):
        """update_maintenance_record updates record fields."""
        from src.database.crud import create_maintenance_record, update_maintenance_record

        record = create_maintenance_record(
            db_session,
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="cleaning",
            description="Original"
        )

        updated = update_maintenance_record(
            db_session,
            record.id,
            description="Updated description",
            done=True,
            cost=10.00
        )

        assert updated is not None
        assert updated.description == "Updated description"
        assert updated.done is True
        assert updated.cost == 10.00

    def test_update_maintenance_record_not_found(self, db_session):
        """update_maintenance_record returns None for nonexistent ID."""
        from src.database.crud import update_maintenance_record

        result = update_maintenance_record(
            db_session,
            99999,
            description="Should not work"
        )

        assert result is None

    def test_delete_maintenance_record(self, db_session, sample_printer):
        """delete_maintenance_record removes a record."""
        from src.database.crud import (
            create_maintenance_record,
            delete_maintenance_record,
            get_maintenance_record
        )

        record = create_maintenance_record(
            db_session,
            printer_id=sample_printer.id,
            date=datetime.utcnow(),
            category="cleaning",
            description="To be deleted"
        )
        record_id = record.id

        result = delete_maintenance_record(db_session, record_id)

        assert result is True
        assert get_maintenance_record(db_session, record_id) is None

    def test_delete_maintenance_record_not_found(self, db_session):
        """delete_maintenance_record returns False for nonexistent ID."""
        from src.database.crud import delete_maintenance_record

        result = delete_maintenance_record(db_session, 99999)

        assert result is False
