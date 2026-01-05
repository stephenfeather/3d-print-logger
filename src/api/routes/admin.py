"""
Admin endpoints for 3D Print Logger.

Provides REST API endpoints for administrative operations,
including API key generation and management.
"""

import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.auth import get_api_key, hash_api_key
from src.api.schemas import ApiKeyCreate, ApiKeyCreated, ApiKeyResponse, SystemInfo
from src.database.crud import create_api_key
from src.database.engine import get_db
from src.database.models import ApiKey, Printer, PrintJob

router = APIRouter()

# Application version
APP_VERSION = "0.1.0"


def generate_api_key() -> str:
    """Generate a new API key with 3dp_ prefix."""
    # 48 random bytes = 64 hex characters
    random_part = secrets.token_hex(32)
    return f"3dp_{random_part}"


@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> List[ApiKeyResponse]:
    """List all API keys (without exposing hashes)."""
    keys = db.query(ApiKey).filter(ApiKey.is_active == True).all()

    return [
        ApiKeyResponse(
            id=key.id,
            key_prefix=key.key_prefix,
            name=key.name,
            is_active=key.is_active,
            expires_at=key.expires_at,
            last_used=key.last_used,
            created_at=key.created_at,
        )
        for key in keys
    ]


@router.post("/api-keys", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_new_api_key(
    key_data: ApiKeyCreate,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> ApiKeyCreated:
    """Create a new API key."""
    # Generate the key
    full_key = generate_api_key()
    key_hash = hash_api_key(full_key)
    key_prefix = full_key[:12]

    # Create in database
    new_key = create_api_key(
        db,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        expires_at=key_data.expires_at,
    )
    db.commit()
    db.refresh(new_key)

    # Return with full key (only time it's shown)
    return ApiKeyCreated(
        id=new_key.id,
        key=full_key,
        key_prefix=key_prefix,
        name=new_key.name,
        is_active=new_key.is_active,
        expires_at=new_key.expires_at,
        last_used=new_key.last_used,
        created_at=new_key.created_at,
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_key: ApiKey = Depends(get_api_key),
) -> None:
    """Revoke (deactivate) an API key."""
    # Find the key
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with id {key_id} not found",
        )

    # Cannot revoke your own key
    if key.id == current_key.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own API key",
        )

    # Deactivate the key
    key.is_active = False
    db.commit()


@router.get("/system", response_model=SystemInfo)
async def get_system_info(
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> SystemInfo:
    """Get system information."""
    # Get database type from engine
    db_type = db.get_bind().dialect.name

    # Get counts
    active_printers = (
        db.query(func.count(Printer.id)).filter(Printer.is_active == True).scalar()
        or 0
    )
    total_jobs = db.query(func.count(PrintJob.id)).scalar() or 0

    return SystemInfo(
        version=APP_VERSION,
        database_type=db_type,
        active_printers=active_printers,
        total_jobs=total_jobs,
        uptime_seconds=None,  # Would require tracking app start time
    )
