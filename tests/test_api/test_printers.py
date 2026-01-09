"""Tests for printer endpoints."""

import pytest
from fastapi import status


class TestListPrinters:
    """Test GET /api/printers endpoint."""

    def test_list_printers_empty(self, client, auth_headers):
        """List printers when none exist."""
        response = client.get("/api/printers", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_printers_with_data(self, client, auth_headers, sample_printer):
        """List printers with existing data."""
        response = client.get("/api/printers", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        printers = response.json()
        assert len(printers) == 1
        assert printers[0]["name"] == "Test Printer"

    def test_list_printers_excludes_inactive(
        self, client, auth_headers, db_session, sample_printer
    ):
        """Inactive printers should be excluded by default."""
        # Create inactive printer
        from src.database.models import Printer

        inactive = Printer(
            name="Inactive Printer",
            moonraker_url="http://inactive:7125",
            is_active=False,
        )
        db_session.add(inactive)
        db_session.commit()

        response = client.get("/api/printers", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        printers = response.json()
        assert len(printers) == 1
        assert printers[0]["name"] == "Test Printer"

    def test_list_printers_include_inactive(
        self, client, auth_headers, db_session, sample_printer
    ):
        """Include inactive printers when requested."""
        from src.database.models import Printer

        inactive = Printer(
            name="Inactive Printer",
            moonraker_url="http://inactive:7125",
            is_active=False,
        )
        db_session.add(inactive)
        db_session.commit()

        response = client.get(
            "/api/printers?include_inactive=true", headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        printers = response.json()
        assert len(printers) == 2


class TestCreatePrinter:
    """Test POST /api/printers endpoint."""

    def test_create_printer_success(self, client, auth_headers):
        """Create a new printer."""
        response = client.post(
            "/api/printers",
            headers=auth_headers,
            json={
                "name": "New Printer",
                "moonraker_url": "http://new-printer:7125",
                "location": "Office",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Printer"
        assert data["moonraker_url"] == "http://new-printer:7125"
        assert data["location"] == "Office"
        assert data["is_active"] is True
        assert "id" in data

    def test_create_printer_minimal(self, client, auth_headers):
        """Create printer with only required fields."""
        response = client.post(
            "/api/printers",
            headers=auth_headers,
            json={
                "name": "Minimal Printer",
                "moonraker_url": "http://minimal:7125",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Minimal Printer"
        assert data["location"] is None

    def test_create_printer_duplicate_name(self, client, auth_headers, sample_printer):
        """Duplicate printer name should return 409."""
        response = client.post(
            "/api/printers",
            headers=auth_headers,
            json={
                "name": "Test Printer",  # Same as sample_printer
                "moonraker_url": "http://duplicate:7125",
            },
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]

    def test_create_printer_invalid_data(self, client, auth_headers):
        """Invalid data should return 422."""
        response = client.post(
            "/api/printers",
            headers=auth_headers,
            json={
                "name": "",  # Empty name
                "moonraker_url": "http://test:7125",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_printer_with_hardware_details(self, client, auth_headers):
        """Create printer with hardware details (Issue #8)."""
        response = client.post(
            "/api/printers",
            headers=auth_headers,
            json={
                "name": "Hardware Printer",
                "moonraker_url": "http://hardware:7125",
                "location": "Workshop",
                # Hardware details
                "printer_type": "FDM",
                "make": "Prusa",
                "model": "MK4",
                "description": "Office printer with enclosure",
                # Specifications
                "filament_diameter": 1.75,
                "nozzle_diameter": 0.4,
                "bed_x": 220.0,
                "bed_y": 220.0,
                "bed_z": 250.0,
                "has_heated_bed": True,
                "has_heated_chamber": False,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Hardware Printer"
        assert data["printer_type"] == "FDM"
        assert data["make"] == "Prusa"
        assert data["model"] == "MK4"
        assert data["description"] == "Office printer with enclosure"
        assert data["filament_diameter"] == 1.75
        assert data["nozzle_diameter"] == 0.4
        assert data["bed_x"] == 220.0
        assert data["bed_y"] == 220.0
        assert data["bed_z"] == 250.0
        assert data["has_heated_bed"] is True
        assert data["has_heated_chamber"] is False

    def test_create_printer_invalid_printer_type(self, client, auth_headers):
        """Invalid printer_type should return 422 (Issue #8)."""
        response = client.post(
            "/api/printers",
            headers=auth_headers,
            json={
                "name": "Invalid Type Printer",
                "moonraker_url": "http://invalid:7125",
                "printer_type": "InvalidType",  # Not in allowed values
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_printer_invalid_filament_diameter(self, client, auth_headers):
        """Invalid filament_diameter should return 422 (Issue #8)."""
        response = client.post(
            "/api/printers",
            headers=auth_headers,
            json={
                "name": "Invalid Filament Printer",
                "moonraker_url": "http://invalid:7125",
                "filament_diameter": 2.0,  # Not in allowed values
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_printer_negative_bed_dimensions(self, client, auth_headers):
        """Negative bed dimensions should return 422 (Issue #8)."""
        response = client.post(
            "/api/printers",
            headers=auth_headers,
            json={
                "name": "Negative Bed Printer",
                "moonraker_url": "http://negative:7125",
                "bed_x": -10,  # Invalid: must be > 0
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetPrinter:
    """Test GET /api/printers/{printer_id} endpoint."""

    def test_get_printer_success(self, client, auth_headers, sample_printer):
        """Get existing printer."""
        response = client.get(
            f"/api/printers/{sample_printer.id}", headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_printer.id
        assert data["name"] == "Test Printer"

    def test_get_printer_not_found(self, client, auth_headers):
        """Non-existent printer should return 404."""
        response = client.get("/api/printers/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdatePrinter:
    """Test PUT /api/printers/{printer_id} endpoint."""

    def test_update_printer_success(self, client, auth_headers, sample_printer):
        """Update existing printer."""
        response = client.put(
            f"/api/printers/{sample_printer.id}",
            headers=auth_headers,
            json={
                "name": "Updated Printer",
                "location": "New Location",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Printer"
        assert data["location"] == "New Location"

    def test_update_printer_partial(self, client, auth_headers, sample_printer):
        """Partial update should only change specified fields."""
        original_url = sample_printer.moonraker_url

        response = client.put(
            f"/api/printers/{sample_printer.id}",
            headers=auth_headers,
            json={"location": "Updated Location Only"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["location"] == "Updated Location Only"
        assert data["moonraker_url"] == original_url  # Unchanged

    def test_update_printer_not_found(self, client, auth_headers):
        """Update non-existent printer should return 404."""
        response = client.put(
            "/api/printers/99999",
            headers=auth_headers,
            json={"name": "Updated"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_printer_duplicate_name(
        self, client, auth_headers, db_session, sample_printer
    ):
        """Update to duplicate name should return 409."""
        from src.database.models import Printer

        other = Printer(
            name="Other Printer", moonraker_url="http://other:7125", is_active=True
        )
        db_session.add(other)
        db_session.commit()

        response = client.put(
            f"/api/printers/{sample_printer.id}",
            headers=auth_headers,
            json={"name": "Other Printer"},  # Duplicate
        )
        assert response.status_code == status.HTTP_409_CONFLICT


class TestDeletePrinter:
    """Test DELETE /api/printers/{printer_id} endpoint."""

    def test_delete_printer_success(self, client, auth_headers, sample_printer):
        """Delete existing printer."""
        response = client.delete(
            f"/api/printers/{sample_printer.id}", headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        response = client.get(
            f"/api/printers/{sample_printer.id}", headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_printer_not_found(self, client, auth_headers):
        """Delete non-existent printer should return 404."""
        response = client.delete("/api/printers/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPrinterStatus:
    """Test GET /api/printers/{printer_id}/status endpoint."""

    def test_get_printer_status(self, client, auth_headers, sample_printer):
        """Get printer status."""
        response = client.get(
            f"/api/printers/{sample_printer.id}/status", headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["printer_id"] == sample_printer.id
        assert data["name"] == "Test Printer"
        assert "is_connected" in data

    def test_get_printer_status_not_found(self, client, auth_headers):
        """Status for non-existent printer should return 404."""
        response = client.get("/api/printers/99999/status", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
