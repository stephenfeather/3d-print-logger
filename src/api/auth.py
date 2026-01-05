"""
API key authentication middleware for 3D Print Logger.

Validates API keys from X-API-Key headers and manages
authentication for protected endpoints.
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from src.database.crud import get_api_key_by_hash, update_api_key_last_used
from src.database.engine import get_db
from src.database.models import ApiKey

# API key header definition
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(key: str) -> str:
    """
    Hash an API key using SHA-256.

    Args:
        key: The API key to hash

    Returns:
        Hex-encoded SHA-256 hash of the key
    """
    return hashlib.sha256(key.encode()).hexdigest()


async def get_api_key(
    x_api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db),
) -> ApiKey:
    """
    Validate API key from X-API-Key header.

    Args:
        x_api_key: API key from header
        db: Database session

    Returns:
        ApiKey model if valid

    Raises:
        HTTPException: If API key is missing, invalid, or expired
    """
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Hash the provided key and look it up
    key_hash = hash_api_key(x_api_key)
    api_key = get_api_key_by_hash(db, key_hash)

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Check expiration
    if api_key.expires_at is not None:
        if datetime.now(timezone.utc) > api_key.expires_at.replace(tzinfo=timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key expired",
                headers={"WWW-Authenticate": "ApiKey"},
            )

    # Update last used timestamp
    update_api_key_last_used(db, api_key.id)

    return api_key
