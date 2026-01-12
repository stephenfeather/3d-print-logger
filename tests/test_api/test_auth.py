"""Tests for API authentication."""

from datetime import datetime, timedelta, UTC

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.database.crud import create_api_key
from src.database.models import ApiKey


class TestHashApiKey:
    """Test API key hashing function."""

    def test_hash_api_key_returns_hex_string(self):
        """hash_api_key should return a hex string."""
        from src.api.auth import hash_api_key

        result = hash_api_key("test_key")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 produces 64 hex chars

    def test_hash_api_key_is_deterministic(self):
        """Same input should produce same hash."""
        from src.api.auth import hash_api_key

        hash1 = hash_api_key("test_key")
        hash2 = hash_api_key("test_key")
        assert hash1 == hash2

    def test_hash_api_key_different_inputs_different_hashes(self):
        """Different inputs should produce different hashes."""
        from src.api.auth import hash_api_key

        hash1 = hash_api_key("key1")
        hash2 = hash_api_key("key2")
        assert hash1 != hash2


class TestApiKeyAuth:
    """Test API key authentication middleware."""

    def test_missing_api_key_returns_401(self, client):
        """Request without API key should return 401."""
        response = client.get("/api/printers")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing API key" in response.json()["detail"]

    def test_invalid_api_key_returns_401(self, client):
        """Request with invalid API key should return 401."""
        response = client.get(
            "/api/printers", headers={"X-API-Key": "invalid_key_12345"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid API key" in response.json()["detail"]

    def test_valid_api_key_succeeds(self, client, auth_headers):
        """Request with valid API key should succeed."""
        response = client.get("/api/printers", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_health_endpoint_no_auth_required(self, client):
        """Health endpoint should not require authentication."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "healthy"

    def test_expired_api_key_returns_401(self, client, db_session):
        """Request with expired API key should return 401."""
        from src.api.auth import hash_api_key

        # Create expired key
        full_key = "3dp_expired123456789012345678901234567890123456789012345"
        key_hash = hash_api_key(full_key)
        create_api_key(
            db_session,
            key_hash=key_hash,
            key_prefix=full_key[:12],
            name="Expired Key",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )

        response = client.get("/api/printers", headers={"X-API-Key": full_key})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in response.json()["detail"].lower()

    def test_api_key_last_used_updated(self, client, db_session, test_api_key):
        """API key last_used should be updated on successful request."""
        # Get the API key before the request
        from src.api.auth import hash_api_key

        key_hash = hash_api_key(test_api_key)
        api_key_before = (
            db_session.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
        )
        last_used_before = api_key_before.last_used

        # Make a request
        response = client.get("/api/printers", headers={"X-API-Key": test_api_key})
        assert response.status_code == status.HTTP_200_OK

        # Refresh and check last_used was updated
        db_session.refresh(api_key_before)
        assert api_key_before.last_used is not None
        if last_used_before is not None:
            assert api_key_before.last_used >= last_used_before
