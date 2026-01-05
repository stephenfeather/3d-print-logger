"""Tests for admin endpoints."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status


class TestApiKeyManagement:
    """Test API key management endpoints."""

    def test_list_api_keys(self, client, auth_headers):
        """List API keys."""
        response = client.get("/api/admin/api-keys", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should include the test API key used for auth
        assert len(data) >= 1
        # Key should not expose full hash
        assert "key_hash" not in data[0]
        assert "key_prefix" in data[0]

    def test_create_api_key(self, client, auth_headers):
        """Create a new API key."""
        response = client.post(
            "/api/admin/api-keys",
            headers=auth_headers,
            json={"name": "New Key"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "key" in data  # Full key returned on creation only
        assert data["key"].startswith("3dp_")
        assert data["name"] == "New Key"
        assert "id" in data

    def test_create_api_key_with_expiration(self, client, auth_headers):
        """Create API key with expiration date."""
        expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        response = client.post(
            "/api/admin/api-keys",
            headers=auth_headers,
            json={"name": "Expiring Key", "expires_at": expires},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["expires_at"] is not None

    def test_revoke_api_key(self, client, auth_headers, db_session):
        """Revoke an API key."""
        from src.api.auth import hash_api_key
        from src.database.crud import create_api_key

        # Create a key to revoke
        key = "3dp_revoke_test1234567890abcdef1234567890abcdef12345678"
        create_api_key(
            db_session,
            key_hash=hash_api_key(key),
            key_prefix=key[:12],
            name="Key to Revoke",
        )
        db_session.commit()

        # Get the key ID
        response = client.get("/api/admin/api-keys", headers=auth_headers)
        keys = response.json()
        key_to_revoke = next(k for k in keys if k["name"] == "Key to Revoke")

        # Revoke the key
        response = client.delete(
            f"/api/admin/api-keys/{key_to_revoke['id']}", headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_revoke_api_key_not_found(self, client, auth_headers):
        """Revoke non-existent API key returns 404."""
        response = client.delete("/api/admin/api-keys/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_revoke_own_key(self, client, auth_headers, db_session):
        """Cannot revoke the API key used for authentication."""
        # Get the current key
        response = client.get("/api/admin/api-keys", headers=auth_headers)
        keys = response.json()
        current_key = next(k for k in keys if k["name"] == "Test API Key")

        # Try to revoke it
        response = client.delete(
            f"/api/admin/api-keys/{current_key['id']}", headers=auth_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "own" in response.json()["detail"].lower()


class TestHealthEndpoint:
    """Test health check endpoint (no auth required)."""

    def test_health_check(self, client):
        """Health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_no_auth_required(self, client):
        """Health check doesn't require authentication."""
        # No auth headers
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK


class TestSystemInfo:
    """Test system info endpoint."""

    def test_system_info(self, client, auth_headers):
        """Get system information."""
        response = client.get("/api/admin/system", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "version" in data
        assert "database_type" in data
        assert "active_printers" in data
        assert "total_jobs" in data
