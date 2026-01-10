"""
Maintenance API endpoints.

Issue #9: Minimal Printer Maintenance Details
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.auth import get_api_key
from src.api.schemas import (
    MaintenanceCreate,
    MaintenanceResponse,
    MaintenanceUpdate,
    PaginatedResponse,
)
from src.database.crud import (
    create_maintenance_record,
    delete_maintenance_record,
    get_maintenance_record,
    get_maintenance_records,
    get_printer,
    update_maintenance_record,
)
from src.database.engine import get_db
from src.database.models import ApiKey, MaintenanceRecord

router = APIRouter()


@router.get("", response_model=PaginatedResponse[MaintenanceResponse])
async def list_maintenance(
    printer_id: Optional[int] = Query(None, description="Filter by printer ID"),
    done: Optional[bool] = Query(None, description="Filter by completion status"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PaginatedResponse[MaintenanceResponse]:
    """
    List maintenance records with optional filters and pagination.
    """
    # Get filtered records
    records = get_maintenance_records(db, printer_id=printer_id, done=done)
    total = len(records)

    # Apply pagination
    paginated = records[offset : offset + limit]

    return PaginatedResponse(
        items=[MaintenanceResponse.model_validate(r) for r in paginated],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(paginated)) < total,
    )


@router.post("", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance(
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> MaintenanceResponse:
    """
    Create a new maintenance record.
    """
    # Verify printer exists
    printer = get_printer(db, data.printer_id)
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with id {data.printer_id} not found",
        )

    record = create_maintenance_record(
        db,
        printer_id=data.printer_id,
        date=data.date,
        category=data.category,
        description=data.description,
        done=data.done,
        cost=data.cost,
        notes=data.notes,
    )

    return MaintenanceResponse.model_validate(record)


@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
async def get_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> MaintenanceResponse:
    """
    Get a maintenance record by ID.
    """
    record = get_maintenance_record(db, maintenance_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance record with id {maintenance_id} not found",
        )

    return MaintenanceResponse.model_validate(record)


@router.put("/{maintenance_id}", response_model=MaintenanceResponse)
async def update_maintenance(
    maintenance_id: int,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> MaintenanceResponse:
    """
    Update a maintenance record.
    """
    # Get only set fields
    update_data = data.model_dump(exclude_unset=True)

    record = update_maintenance_record(db, maintenance_id, **update_data)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance record with id {maintenance_id} not found",
        )

    return MaintenanceResponse.model_validate(record)


@router.delete("/{maintenance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> None:
    """
    Delete a maintenance record.
    """
    deleted = delete_maintenance_record(db, maintenance_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance record with id {maintenance_id} not found",
        )
