"""
TDD tests for maintenance API endpoints.

Issue #9: Minimal Printer Maintenance Details

Following Test-Driven Development: Tests written FIRST before implementation.
"""

import pytest
from datetime import datetime, timezone
from fastapi import status


class TestListMaintenance:
    """Test GET /api/maintenance endpoint."""

    def test_list_maintenance_empty(self, client, auth_headers):
        """List maintenance when none exist."""
        response = client.get("/api/maintenance", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_maintenance_with_data(self, client, auth_headers, db_session, sample_printer):
        """List maintenance records with existing data."""
        from src.database.models import MaintenanceRecord

        record = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.now(timezone.utc),
            category="cleaning",
            description="Test cleaning"
        )
        db_session.add(record)
        db_session.commit()

        response = client.get("/api/maintenance", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["category"] == "cleaning"
        assert data["total"] == 1

    def test_list_maintenance_filter_by_printer(self, client, auth_headers, db_session):
        """Filter maintenance records by printer."""
        from src.database.models import Printer, MaintenanceRecord

        printer1 = Printer(name="Printer 1", moonraker_url="http://p1:7125")
        printer2 = Printer(name="Printer 2", moonraker_url="http://p2:7125")
        db_session.add_all([printer1, printer2])
        db_session.commit()

        record1 = MaintenanceRecord(
            printer_id=printer1.id,
            date=datetime.now(timezone.utc),
            category="cleaning",
            description="P1 cleaning"
        )
        record2 = MaintenanceRecord(
            printer_id=printer2.id,
            date=datetime.now(timezone.utc),
            category="calibration",
            description="P2 calibration"
        )
        db_session.add_all([record1, record2])
        db_session.commit()

        response = client.get(
            f"/api/maintenance?printer_id={printer1.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["description"] == "P1 cleaning"

    def test_list_maintenance_filter_by_done(self, client, auth_headers, db_session, sample_printer):
        """Filter maintenance records by done status."""
        from src.database.models import MaintenanceRecord

        record1 = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.now(timezone.utc),
            category="cleaning",
            description="Done cleaning",
            done=True
        )
        record2 = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.now(timezone.utc),
            category="calibration",
            description="Pending calibration",
            done=False
        )
        db_session.add_all([record1, record2])
        db_session.commit()

        response = client.get("/api/maintenance?done=true", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["description"] == "Done cleaning"

    def test_list_maintenance_pagination(self, client, auth_headers, db_session, sample_printer):
        """Test pagination for maintenance records."""
        from src.database.models import MaintenanceRecord

        # Create 5 records
        for i in range(5):
            db_session.add(MaintenanceRecord(
                printer_id=sample_printer.id,
                date=datetime.now(timezone.utc),
                category=f"category-{i}",
                description=f"Description {i}"
            ))
        db_session.commit()

        response = client.get("/api/maintenance?limit=2&offset=0", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["has_more"] is True

    def test_list_maintenance_requires_auth(self, client):
        """Endpoint requires authentication."""
        response = client.get("/api/maintenance")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateMaintenance:
    """Test POST /api/maintenance endpoint."""

    def test_create_maintenance_success(self, client, auth_headers, sample_printer):
        """Create a new maintenance record."""
        response = client.post(
            "/api/maintenance",
            headers=auth_headers,
            json={
                "printer_id": sample_printer.id,
                "date": datetime.now(timezone.utc).isoformat(),
                "category": "cleaning",
                "description": "Nozzle cleaning"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["category"] == "cleaning"
        assert data["description"] == "Nozzle cleaning"
        assert data["done"] is False
        assert "id" in data

    def test_create_maintenance_all_fields(self, client, auth_headers, sample_printer):
        """Create maintenance record with all fields."""
        response = client.post(
            "/api/maintenance",
            headers=auth_headers,
            json={
                "printer_id": sample_printer.id,
                "date": datetime.now(timezone.utc).isoformat(),
                "category": "parts_replacement",
                "description": "New nozzle installed",
                "done": True,
                "cost": 5.99,
                "notes": "0.4mm brass nozzle"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["done"] is True
        assert data["cost"] == 5.99
        assert data["notes"] == "0.4mm brass nozzle"

    def test_create_maintenance_invalid_printer(self, client, auth_headers):
        """Invalid printer_id returns 404."""
        response = client.post(
            "/api/maintenance",
            headers=auth_headers,
            json={
                "printer_id": 99999,
                "date": datetime.now(timezone.utc).isoformat(),
                "category": "cleaning",
                "description": "Test"
            }
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_maintenance_missing_required(self, client, auth_headers, sample_printer):
        """Missing required fields returns 422."""
        response = client.post(
            "/api/maintenance",
            headers=auth_headers,
            json={
                "printer_id": sample_printer.id
                # Missing date, category, description
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_maintenance_negative_cost(self, client, auth_headers, sample_printer):
        """Negative cost returns 422."""
        response = client.post(
            "/api/maintenance",
            headers=auth_headers,
            json={
                "printer_id": sample_printer.id,
                "date": datetime.now(timezone.utc).isoformat(),
                "category": "repair",
                "description": "Test",
                "cost": -10.00
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetMaintenance:
    """Test GET /api/maintenance/{id} endpoint."""

    def test_get_maintenance_success(self, client, auth_headers, db_session, sample_printer):
        """Get a maintenance record by ID."""
        from src.database.models import MaintenanceRecord

        record = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.now(timezone.utc),
            category="calibration",
            description="Test record"
        )
        db_session.add(record)
        db_session.commit()

        response = client.get(f"/api/maintenance/{record.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == record.id
        assert data["category"] == "calibration"

    def test_get_maintenance_not_found(self, client, auth_headers):
        """Non-existent ID returns 404."""
        response = client.get("/api/maintenance/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateMaintenance:
    """Test PUT /api/maintenance/{id} endpoint."""

    def test_update_maintenance_success(self, client, auth_headers, db_session, sample_printer):
        """Update a maintenance record."""
        from src.database.models import MaintenanceRecord

        record = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.now(timezone.utc),
            category="cleaning",
            description="Original"
        )
        db_session.add(record)
        db_session.commit()

        response = client.put(
            f"/api/maintenance/{record.id}",
            headers=auth_headers,
            json={
                "description": "Updated description",
                "done": True,
                "cost": 10.00
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["done"] is True
        assert data["cost"] == 10.00

    def test_update_maintenance_partial(self, client, auth_headers, db_session, sample_printer):
        """Partial update only changes specified fields."""
        from src.database.models import MaintenanceRecord

        record = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.now(timezone.utc),
            category="repair",
            description="Original description",
            cost=50.00
        )
        db_session.add(record)
        db_session.commit()

        response = client.put(
            f"/api/maintenance/{record.id}",
            headers=auth_headers,
            json={"done": True}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["done"] is True
        assert data["description"] == "Original description"  # Unchanged
        assert data["cost"] == 50.00  # Unchanged

    def test_update_maintenance_not_found(self, client, auth_headers):
        """Non-existent ID returns 404."""
        response = client.put(
            "/api/maintenance/99999",
            headers=auth_headers,
            json={"done": True}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteMaintenance:
    """Test DELETE /api/maintenance/{id} endpoint."""

    def test_delete_maintenance_success(self, client, auth_headers, db_session, sample_printer):
        """Delete a maintenance record."""
        from src.database.models import MaintenanceRecord

        record = MaintenanceRecord(
            printer_id=sample_printer.id,
            date=datetime.now(timezone.utc),
            category="cleaning",
            description="To delete"
        )
        db_session.add(record)
        db_session.commit()
        record_id = record.id

        response = client.delete(f"/api/maintenance/{record_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        response = client.get(f"/api/maintenance/{record_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_maintenance_not_found(self, client, auth_headers):
        """Non-existent ID returns 404."""
        response = client.delete("/api/maintenance/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestMaintenanceAuth:
    """Test authentication for maintenance endpoints."""

    def test_list_without_auth(self, client):
        """List requires auth."""
        response = client.get("/api/maintenance")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_without_auth(self, client):
        """Create requires auth."""
        response = client.post("/api/maintenance", json={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_without_auth(self, client):
        """Get requires auth."""
        response = client.get("/api/maintenance/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_without_auth(self, client):
        """Update requires auth."""
        response = client.put("/api/maintenance/1", json={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_without_auth(self, client):
        """Delete requires auth."""
        response = client.delete("/api/maintenance/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
