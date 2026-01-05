# Phase 3: FastAPI REST API Layer Implementation Plan

**Created**: 2026-01-05
**Status**: Ready for implementation
**Previous Phases**: Phase 1 (Database - 70 tests), Phase 2 (Moonraker WebSocket - 48/50 tests)

## Overview

Implement a complete FastAPI REST API layer for the 3D Print Logger, including authentication, CRUD endpoints for printers and jobs, analytics endpoints, and admin functionality. This phase builds upon the completed database layer (Phase 1) and Moonraker integration (Phase 2).

## Current State Analysis

### Existing Infrastructure
- **Database layer**: Complete with 5 SQLAlchemy models (Printer, PrintJob, JobDetails, JobTotals, ApiKey)
- **CRUD operations**: 11 functions in `src/database/crud.py`
- **Moonraker integration**: WebSocket client, event handlers, connection manager
- **Configuration**: `src/config.py` with ApiConfig dataclass (host, port, cors_origins)
- **Database session**: `get_db()` dependency already implemented in `src/database/engine.py`

### API Skeleton (Empty Stubs)
- `src/api/__init__.py` - empty
- `src/api/auth.py` - docstring only
- `src/api/routes/__init__.py` - empty
- `src/api/routes/printers.py` - docstring only
- `src/api/routes/jobs.py` - docstring only
- `src/api/routes/analytics.py` - docstring only
- `src/api/routes/admin.py` - docstring only

### Key Discoveries
- ApiKey model stores SHA-256 hash with `key_prefix` for display (e.g., "3dp_abc12345...")
- `get_api_key_by_hash()` in crud.py only returns active keys
- `update_api_key_last_used()` exists for tracking API key usage
- Jobs support filtering by `status` and ordering by `start_time` descending
- FastAPI lifecycle events use `@asynccontextmanager` with `lifespan` parameter (not deprecated `on_event`)

## Desired End State

After Phase 3 completion:
1. FastAPI application starts correctly with database initialization and Moonraker manager
2. All API endpoints protected by API key authentication (except `/health`)
3. CRUD operations for printers with real-time status integration
4. Job listing with pagination, filtering, and details
5. Analytics endpoints for per-printer and aggregate statistics
6. Admin endpoints for API key management
7. Comprehensive test suite with 90%+ coverage
8. Pydantic schemas for all request/response models

### Verification Commands
```bash
# All tests pass
uv run pytest tests/test_api/ -v --cov=src/api --cov-report=term-missing

# Coverage > 90%
uv run pytest tests/ -v --cov=src --cov-fail-under=90

# Application starts without errors
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000

# OpenAPI docs accessible
curl http://localhost:8000/docs
```

## What We're NOT Doing

- **Rate limiting**: Deferred to production hardening phase (not MVP)
- **WebSocket/SSE for real-time updates**: Deferred to Phase 5 (Frontend)
- **Gcode file upload**: Deferred to Phase 4 (Parser)
- **Multi-user/RBAC**: Single-user design per original requirements
- **Refresh tokens**: Simple API key auth is sufficient

## Design Decisions (Resolving UNCONFIRMED Items)

### 1. API Key Authentication Format
**Decision**: Use `X-API-Key` header (not Bearer)

**Rationale**:
- Simpler for service-to-service communication (3D Print Logger use case)
- No OAuth2 flow complexity needed for single-user application
- FastAPI's `APIKeyHeader` provides clean implementation
- Bearer token pattern better suited for OAuth2/JWT flows

**Implementation**: `X-API-Key: 3dp_abc123...`

### 2. Pagination Strategy
**Decision**: Offset-based pagination with `limit`/`offset` parameters

**Rationale**:
- Simpler implementation for MVP
- Print job history is append-only (no deletions affecting page consistency)
- Users may want to jump to specific pages in UI
- Dataset size is typically small-medium (thousands, not millions)
- Cursor-based can be added later if needed

**Implementation**: `?limit=20&offset=0` with `Link` headers for pagination

### 3. Rate Limiting
**Decision**: Defer to production phase

**Rationale**:
- Self-hosted application on local network
- Single-user design limits abuse vectors
- Can add via SlowAPI when deploying to cloud

### 4. Real-time Updates
**Decision**: Defer WebSocket/SSE to Phase 5 (Frontend)

**Rationale**:
- REST API sufficient for current requirements
- Real-time updates primarily needed for dashboard UI
- MoonrakerManager already handles printer status internally
- Can expose `/printers/{id}/status` for polling

## Implementation Approach

Follow TDD workflow: Write failing tests first, implement minimal code to pass, refactor.

### Dependency Injection Strategy
```python
# Database session dependency (existing)
def get_db() -> Generator[Session, None, None]: ...

# API key authentication dependency (new)
async def get_api_key(x_api_key: str = Security(api_key_header)) -> ApiKey: ...

# Current printer status from manager (new)
def get_moonraker_manager() -> MoonrakerManager: ...
```

---

## Phase 3.1: Core Application Setup & Authentication

### Overview
Set up the FastAPI application with proper lifecycle management and API key authentication middleware.

### Changes Required

#### 1. FastAPI Application Entry Point
**File**: `src/main.py`
**Changes**: Complete implementation with lifespan context manager

```python
"""
FastAPI application entry point for 3D Print Logger.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import admin, analytics, jobs, printers
from src.config import get_config
from src.database.engine import async_init_database
from src.moonraker.manager import MoonrakerManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    await async_init_database()
    # Note: Moonraker manager start moved to background task
    # to avoid blocking startup if printers are offline
    yield
    # Shutdown
    manager = MoonrakerManager.get_instance()
    await manager.stop()


app = FastAPI(
    title="3D Print Logger",
    description="Self-hosted application for logging and analyzing 3D print jobs",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(printers.router, prefix="/api/printers", tags=["printers"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint (no auth required)."""
    return {"status": "healthy"}


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
```

#### 2. API Key Authentication
**File**: `src/api/auth.py`
**Changes**: Implement X-API-Key header authentication

```python
"""
API key authentication middleware for 3D Print Logger.
"""

import hashlib
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
    """Hash an API key using SHA-256."""
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
        from datetime import datetime
        if datetime.utcnow() > api_key.expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key expired",
                headers={"WWW-Authenticate": "ApiKey"},
            )

    # Update last used timestamp
    update_api_key_last_used(db, api_key.id)

    return api_key
```

#### 3. Pydantic Schemas Base
**File**: `src/api/schemas.py` (NEW)
**Changes**: Create base schemas and common types

```python
"""
Pydantic schemas for API request/response models.
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# Generic type for paginated responses
T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)


# ========== Pagination ==========

class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool


# ========== Error Responses ==========

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    detail: List[dict[str, Any]]


# ========== Common Fields ==========

class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime
    updated_at: datetime
```

### Success Criteria

#### Automated Verification
- [ ] Tests pass: `uv run pytest tests/test_api/test_auth.py -v`
- [ ] Tests pass: `uv run pytest tests/test_api/test_main.py -v`
- [ ] Application starts: `uv run uvicorn src.main:app --port 8000`
- [ ] Health endpoint works: `curl http://localhost:8000/health`
- [ ] Type checking passes: `uv run mypy src/api/`

#### Manual Verification
- [ ] OpenAPI docs load at `/docs`
- [ ] Requests without API key return 401
- [ ] Requests with invalid API key return 401
- [ ] Requests with valid API key succeed

**Implementation Note**: After completing this phase and all automated verification passes, pause for manual confirmation before proceeding.

---

## Phase 3.2: Printer Endpoints

### Overview
Implement CRUD endpoints for printer management with status integration.

### Changes Required

#### 1. Printer Schemas
**File**: `src/api/schemas.py` (APPEND)
**Changes**: Add printer request/response schemas

```python
# ========== Printer Schemas ==========

class PrinterBase(BaseSchema):
    """Base printer fields."""
    name: str = Field(..., min_length=1, max_length=100)
    moonraker_url: str = Field(..., min_length=1, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    moonraker_api_key: Optional[str] = Field(None, max_length=200)
    is_active: bool = True


class PrinterCreate(PrinterBase):
    """Schema for creating a printer."""
    pass


class PrinterUpdate(BaseSchema):
    """Schema for updating a printer (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    moonraker_url: Optional[str] = Field(None, min_length=1, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    moonraker_api_key: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class PrinterResponse(PrinterBase, TimestampMixin):
    """Schema for printer response."""
    id: int
    last_seen: Optional[datetime] = None


class PrinterStatusResponse(BaseSchema):
    """Schema for printer status response."""
    printer_id: int
    name: str
    is_connected: bool
    state: Optional[str] = None  # standby, printing, paused, error, complete
    current_job: Optional[str] = None
    progress: Optional[float] = None
    last_seen: Optional[datetime] = None
```

#### 2. Extended CRUD Operations
**File**: `src/database/crud.py` (APPEND)
**Changes**: Add missing CRUD operations for API

```python
# ========== Additional Printer CRUD ==========

def get_all_printers(db: Session, include_inactive: bool = False) -> List[Printer]:
    """
    Get all printers, optionally including inactive ones.

    Args:
        db: Database session
        include_inactive: If True, include inactive printers

    Returns:
        List of Printer instances
    """
    query = db.query(Printer)
    if not include_inactive:
        query = query.filter(Printer.is_active == True)
    return query.order_by(Printer.name).all()


def update_printer(db: Session, printer_id: int, **update_data) -> Optional[Printer]:
    """
    Update a printer's fields.

    Args:
        db: Database session
        printer_id: Printer ID to update
        **update_data: Fields to update

    Returns:
        Updated Printer if found, None otherwise
    """
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if printer is None:
        return None

    for key, value in update_data.items():
        if value is not None:
            setattr(printer, key, value)

    db.commit()
    db.refresh(printer)
    return printer


def delete_printer(db: Session, printer_id: int) -> bool:
    """
    Delete a printer by ID.

    Args:
        db: Database session
        printer_id: Printer ID to delete

    Returns:
        True if deleted, False if not found
    """
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if printer is None:
        return False

    db.delete(printer)
    db.commit()
    return True


def get_printer_by_name(db: Session, name: str) -> Optional[Printer]:
    """
    Get a printer by its name.

    Args:
        db: Database session
        name: Printer name to look up

    Returns:
        Printer if found, None otherwise
    """
    return db.query(Printer).filter(Printer.name == name).first()
```

#### 3. Printer Routes
**File**: `src/api/routes/printers.py`
**Changes**: Implement full CRUD endpoints

```python
"""
Printer CRUD endpoints for 3D Print Logger.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.auth import get_api_key
from src.api.schemas import (
    PrinterCreate,
    PrinterResponse,
    PrinterStatusResponse,
    PrinterUpdate,
)
from src.database.crud import (
    create_printer,
    delete_printer,
    get_all_printers,
    get_printer,
    get_printer_by_name,
    update_printer,
)
from src.database.engine import get_db
from src.database.models import ApiKey
from src.moonraker.manager import MoonrakerManager

router = APIRouter()


@router.get("", response_model=List[PrinterResponse])
async def list_printers(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> List[PrinterResponse]:
    """List all printers."""
    printers = get_all_printers(db, include_inactive=include_inactive)
    return printers


@router.post("", response_model=PrinterResponse, status_code=status.HTTP_201_CREATED)
async def create_new_printer(
    printer_data: PrinterCreate,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PrinterResponse:
    """Create a new printer."""
    # Check for duplicate name
    existing = get_printer_by_name(db, printer_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Printer with name '{printer_data.name}' already exists",
        )

    printer = create_printer(db, **printer_data.model_dump())
    return printer


@router.get("/{printer_id}", response_model=PrinterResponse)
async def get_printer_by_id(
    printer_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PrinterResponse:
    """Get a specific printer by ID."""
    printer = get_printer(db, printer_id)
    if printer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with ID {printer_id} not found",
        )
    return printer


@router.put("/{printer_id}", response_model=PrinterResponse)
async def update_printer_by_id(
    printer_id: int,
    printer_data: PrinterUpdate,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PrinterResponse:
    """Update a printer."""
    # Check if new name conflicts with existing printer
    if printer_data.name:
        existing = get_printer_by_name(db, printer_data.name)
        if existing and existing.id != printer_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Printer with name '{printer_data.name}' already exists",
            )

    printer = update_printer(
        db, printer_id, **printer_data.model_dump(exclude_unset=True)
    )
    if printer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with ID {printer_id} not found",
        )
    return printer


@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_printer_by_id(
    printer_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> None:
    """Delete a printer."""
    deleted = delete_printer(db, printer_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with ID {printer_id} not found",
        )


@router.get("/{printer_id}/status", response_model=PrinterStatusResponse)
async def get_printer_status(
    printer_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PrinterStatusResponse:
    """Get real-time status of a printer."""
    printer = get_printer(db, printer_id)
    if printer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with ID {printer_id} not found",
        )

    # Get status from Moonraker manager
    manager = MoonrakerManager.get_instance()
    is_connected = printer_id in manager.clients

    # TODO: Get actual status from client when implemented
    return PrinterStatusResponse(
        printer_id=printer.id,
        name=printer.name,
        is_connected=is_connected,
        state=None,  # Would come from client.get_status()
        current_job=None,
        progress=None,
        last_seen=printer.last_seen,
    )


@router.post("/{printer_id}/connect", status_code=status.HTTP_202_ACCEPTED)
async def connect_printer(
    printer_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> dict:
    """Initiate connection to a printer."""
    printer = get_printer(db, printer_id)
    if printer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with ID {printer_id} not found",
        )

    manager = MoonrakerManager.get_instance()

    # Check if already connected
    if printer_id in manager.clients:
        return {"message": "Printer already connected", "status": "connected"}

    try:
        await manager.connect_printer(printer)
        return {"message": "Connection initiated", "status": "connecting"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to printer: {str(e)}",
        )


@router.post("/{printer_id}/disconnect", status_code=status.HTTP_202_ACCEPTED)
async def disconnect_printer(
    printer_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> dict:
    """Disconnect from a printer."""
    printer = get_printer(db, printer_id)
    if printer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with ID {printer_id} not found",
        )

    manager = MoonrakerManager.get_instance()

    if printer_id not in manager.clients:
        return {"message": "Printer not connected", "status": "disconnected"}

    await manager.disconnect_printer(printer_id)
    return {"message": "Disconnected", "status": "disconnected"}
```

### Success Criteria

#### Automated Verification
- [ ] Tests pass: `uv run pytest tests/test_api/test_printers.py -v`
- [ ] Tests pass: `uv run pytest tests/test_database/test_crud.py -v` (new CRUD tests)
- [ ] Type checking passes: `uv run mypy src/api/routes/printers.py`

#### Manual Verification
- [ ] GET /api/printers returns list of printers
- [ ] POST /api/printers creates a new printer
- [ ] GET /api/printers/{id} returns specific printer
- [ ] PUT /api/printers/{id} updates printer
- [ ] DELETE /api/printers/{id} removes printer
- [ ] GET /api/printers/{id}/status returns connection status

**Implementation Note**: After completing this phase and all automated verification passes, pause for manual confirmation before proceeding.

---

## Phase 3.3: Job Endpoints

### Overview
Implement job listing with pagination, filtering, and detail retrieval.

### Changes Required

#### 1. Job Schemas
**File**: `src/api/schemas.py` (APPEND)
**Changes**: Add job request/response schemas

```python
# ========== Job Schemas ==========

class JobBase(BaseSchema):
    """Base job fields."""
    job_id: str
    filename: str
    status: str
    user: Optional[str] = None


class JobResponse(JobBase, TimestampMixin):
    """Schema for job response."""
    id: int
    printer_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    print_duration: Optional[float] = None
    total_duration: Optional[float] = None
    filament_used: Optional[float] = None
    job_metadata: Optional[dict] = None
    auxiliary_data: Optional[dict] = None


class JobDetailResponse(BaseSchema):
    """Schema for job details response."""
    id: int
    print_job_id: int
    layer_height: Optional[float] = None
    first_layer_height: Optional[float] = None
    nozzle_temp: Optional[int] = None
    bed_temp: Optional[int] = None
    print_speed: Optional[int] = None
    infill_percentage: Optional[int] = None
    infill_pattern: Optional[str] = None
    support_enabled: Optional[bool] = None
    support_type: Optional[str] = None
    filament_type: Optional[str] = None
    filament_brand: Optional[str] = None
    filament_color: Optional[str] = None
    estimated_time: Optional[int] = None
    estimated_filament: Optional[float] = None
    layer_count: Optional[int] = None
    object_height: Optional[float] = None
    raw_metadata: Optional[dict] = None


class JobWithDetailsResponse(JobResponse):
    """Schema for job with details included."""
    details: Optional[JobDetailResponse] = None


class JobFilterParams(BaseModel):
    """Query parameters for job filtering."""
    printer_id: Optional[int] = None
    status: Optional[str] = Field(
        None,
        description="Filter by status: printing, paused, completed, error, cancelled"
    )
    start_date: Optional[datetime] = Field(None, description="Filter jobs starting after this date")
    end_date: Optional[datetime] = Field(None, description="Filter jobs starting before this date")
```

#### 2. Extended Job CRUD Operations
**File**: `src/database/crud.py` (APPEND)
**Changes**: Add paginated job queries

```python
# ========== Extended Job CRUD ==========

from sqlalchemy import func

def get_jobs_paginated(
    db: Session,
    limit: int = 20,
    offset: int = 0,
    printer_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> tuple[List[PrintJob], int]:
    """
    Get paginated jobs with optional filters.

    Args:
        db: Database session
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        printer_id: Filter by printer ID
        status: Filter by job status
        start_date: Filter by start_time >= date
        end_date: Filter by start_time <= date

    Returns:
        Tuple of (list of jobs, total count)
    """
    query = db.query(PrintJob)

    # Apply filters
    if printer_id is not None:
        query = query.filter(PrintJob.printer_id == printer_id)
    if status is not None:
        query = query.filter(PrintJob.status == status)
    if start_date is not None:
        query = query.filter(PrintJob.start_time >= start_date)
    if end_date is not None:
        query = query.filter(PrintJob.start_time <= end_date)

    # Get total count before pagination
    total = query.count()

    # Apply ordering and pagination
    jobs = query.order_by(PrintJob.start_time.desc()).offset(offset).limit(limit).all()

    return jobs, total


def get_job_by_id(db: Session, job_id: int) -> Optional[PrintJob]:
    """
    Get a job by its database ID.

    Args:
        db: Database session
        job_id: Job database ID

    Returns:
        PrintJob if found, None otherwise
    """
    return db.query(PrintJob).filter(PrintJob.id == job_id).first()


def get_job_details(db: Session, print_job_id: int) -> Optional[JobDetails]:
    """
    Get job details for a print job.

    Args:
        db: Database session
        print_job_id: Print job ID

    Returns:
        JobDetails if found, None otherwise
    """
    return db.query(JobDetails).filter(JobDetails.print_job_id == print_job_id).first()


def delete_job(db: Session, job_id: int) -> bool:
    """
    Delete a job by ID.

    Args:
        db: Database session
        job_id: Job database ID to delete

    Returns:
        True if deleted, False if not found
    """
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if job is None:
        return False

    db.delete(job)
    db.commit()
    return True
```

#### 3. Job Routes
**File**: `src/api/routes/jobs.py`
**Changes**: Implement job listing and retrieval endpoints

```python
"""
Job query endpoints for 3D Print Logger.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.auth import get_api_key
from src.api.schemas import (
    JobDetailResponse,
    JobResponse,
    JobWithDetailsResponse,
    PaginatedResponse,
    PaginationParams,
)
from src.database.crud import (
    delete_job,
    get_job_by_id,
    get_job_details,
    get_jobs_paginated,
)
from src.database.engine import get_db
from src.database.models import ApiKey

router = APIRouter()


@router.get("", response_model=PaginatedResponse[JobResponse])
async def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    printer_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PaginatedResponse[JobResponse]:
    """
    List jobs with pagination and filtering.

    Filters:
    - printer_id: Filter by printer
    - status: Filter by status (printing, paused, completed, error, cancelled)
    - start_date: Jobs started on or after this date
    - end_date: Jobs started on or before this date
    """
    jobs, total = get_jobs_paginated(
        db,
        limit=limit,
        offset=offset,
        printer_id=printer_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )

    return PaginatedResponse(
        items=jobs,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(jobs)) < total,
    )


@router.get("/{job_id}", response_model=JobWithDetailsResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> JobWithDetailsResponse:
    """Get a specific job by ID, including details if available."""
    job = get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found",
        )

    # Get details if available
    details = get_job_details(db, job_id)

    response = JobWithDetailsResponse.model_validate(job)
    if details:
        response.details = JobDetailResponse.model_validate(details)

    return response


@router.get("/{job_id}/details", response_model=JobDetailResponse)
async def get_job_details_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> JobDetailResponse:
    """Get extended details for a job (slicer settings, etc.)."""
    job = get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found",
        )

    details = get_job_details(db, job_id)
    if details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Details not available for job {job_id}",
        )

    return details


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> None:
    """Delete a job record."""
    deleted = delete_job(db, job_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found",
        )
```

### Success Criteria

#### Automated Verification
- [ ] Tests pass: `uv run pytest tests/test_api/test_jobs.py -v`
- [ ] Tests pass: `uv run pytest tests/test_database/test_crud.py -v` (new CRUD tests)
- [ ] Type checking passes: `uv run mypy src/api/routes/jobs.py`

#### Manual Verification
- [ ] GET /api/jobs returns paginated job list
- [ ] GET /api/jobs?printer_id=1 filters by printer
- [ ] GET /api/jobs?status=completed filters by status
- [ ] GET /api/jobs/{id} returns job with details
- [ ] GET /api/jobs/{id}/details returns extended metadata
- [ ] DELETE /api/jobs/{id} removes job

**Implementation Note**: After completing this phase and all automated verification passes, pause for manual confirmation before proceeding.

---

## Phase 3.4: Analytics Endpoints

### Overview
Implement analytics endpoints for statistics and insights.

### Changes Required

#### 1. Analytics Schemas
**File**: `src/api/schemas.py` (APPEND)
**Changes**: Add analytics response schemas

```python
# ========== Analytics Schemas ==========

class PrinterStatsResponse(BaseSchema):
    """Statistics for a single printer."""
    printer_id: int
    printer_name: str
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    total_print_time: float  # seconds
    total_filament_used: float  # mm
    success_rate: float  # percentage
    average_job_duration: Optional[float] = None  # seconds
    longest_job: float  # seconds


class AggregateStatsResponse(BaseSchema):
    """Aggregate statistics across all printers."""
    total_printers: int
    active_printers: int
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    total_print_time: float
    total_filament_used: float
    overall_success_rate: float


class FilamentUsageResponse(BaseSchema):
    """Filament usage breakdown by type."""
    filament_type: str
    total_used: float  # mm
    job_count: int
    average_per_job: float  # mm


class TimelineDataPoint(BaseSchema):
    """Single data point for timeline chart."""
    date: str  # ISO format date
    job_count: int
    successful: int
    failed: int
    print_time: float


class TimelineResponse(BaseSchema):
    """Timeline data for charts."""
    period: str  # daily, weekly, monthly
    data: List[TimelineDataPoint]
```

#### 2. Analytics CRUD Operations
**File**: `src/database/crud.py` (APPEND)
**Changes**: Add analytics queries

```python
# ========== Analytics Queries ==========

from sqlalchemy import case, extract

def get_job_stats_by_printer(db: Session, printer_id: int) -> dict:
    """
    Get job statistics for a specific printer.

    Args:
        db: Database session
        printer_id: Printer ID

    Returns:
        Dictionary with statistics
    """
    from src.database.models import Printer

    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        return None

    # Get totals from job_totals table
    totals = db.query(JobTotals).filter(JobTotals.printer_id == printer_id).first()

    # Get job counts by status
    status_counts = db.query(
        PrintJob.status,
        func.count(PrintJob.id).label("count")
    ).filter(
        PrintJob.printer_id == printer_id
    ).group_by(PrintJob.status).all()

    status_dict = {s.status: s.count for s in status_counts}

    total_jobs = sum(status_dict.values())
    successful = status_dict.get("completed", 0)
    failed = status_dict.get("error", 0)
    cancelled = status_dict.get("cancelled", 0)

    success_rate = (successful / total_jobs * 100) if total_jobs > 0 else 0.0
    avg_duration = None
    if totals and totals.total_jobs > 0:
        avg_duration = totals.total_time / totals.total_jobs

    return {
        "printer_id": printer_id,
        "printer_name": printer.name,
        "total_jobs": total_jobs,
        "successful_jobs": successful,
        "failed_jobs": failed,
        "cancelled_jobs": cancelled,
        "total_print_time": totals.total_print_time if totals else 0.0,
        "total_filament_used": totals.total_filament_used if totals else 0.0,
        "success_rate": round(success_rate, 2),
        "average_job_duration": avg_duration,
        "longest_job": totals.longest_job if totals else 0.0,
    }


def get_aggregate_stats(db: Session) -> dict:
    """
    Get aggregate statistics across all printers.

    Args:
        db: Database session

    Returns:
        Dictionary with aggregate statistics
    """
    from src.database.models import Printer

    # Printer counts
    total_printers = db.query(Printer).count()
    active_printers = db.query(Printer).filter(Printer.is_active == True).count()

    # Job counts by status
    status_counts = db.query(
        PrintJob.status,
        func.count(PrintJob.id).label("count")
    ).group_by(PrintJob.status).all()

    status_dict = {s.status: s.count for s in status_counts}

    total_jobs = sum(status_dict.values())
    successful = status_dict.get("completed", 0)
    failed = status_dict.get("error", 0)
    cancelled = status_dict.get("cancelled", 0)

    # Aggregate totals
    totals_sum = db.query(
        func.sum(JobTotals.total_print_time).label("print_time"),
        func.sum(JobTotals.total_filament_used).label("filament"),
    ).first()

    success_rate = (successful / total_jobs * 100) if total_jobs > 0 else 0.0

    return {
        "total_printers": total_printers,
        "active_printers": active_printers,
        "total_jobs": total_jobs,
        "successful_jobs": successful,
        "failed_jobs": failed,
        "cancelled_jobs": cancelled,
        "total_print_time": totals_sum.print_time or 0.0,
        "total_filament_used": totals_sum.filament or 0.0,
        "overall_success_rate": round(success_rate, 2),
    }


def get_filament_usage_breakdown(db: Session) -> List[dict]:
    """
    Get filament usage breakdown by filament type.

    Args:
        db: Database session

    Returns:
        List of filament usage dictionaries
    """
    results = db.query(
        JobDetails.filament_type,
        func.count(JobDetails.id).label("job_count"),
        func.sum(PrintJob.filament_used).label("total_used"),
    ).join(
        PrintJob, JobDetails.print_job_id == PrintJob.id
    ).filter(
        JobDetails.filament_type.isnot(None),
        PrintJob.status == "completed",
    ).group_by(
        JobDetails.filament_type
    ).all()

    return [
        {
            "filament_type": r.filament_type,
            "total_used": r.total_used or 0.0,
            "job_count": r.job_count,
            "average_per_job": (r.total_used / r.job_count) if r.job_count > 0 else 0.0,
        }
        for r in results
    ]


def get_jobs_timeline(
    db: Session,
    days: int = 30,
) -> List[dict]:
    """
    Get job counts by day for timeline chart.

    Args:
        db: Database session
        days: Number of days to include

    Returns:
        List of daily statistics
    """
    from datetime import timedelta

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get daily job counts
    results = db.query(
        func.date(PrintJob.start_time).label("date"),
        func.count(PrintJob.id).label("total"),
        func.sum(case((PrintJob.status == "completed", 1), else_=0)).label("successful"),
        func.sum(case((PrintJob.status == "error", 1), else_=0)).label("failed"),
        func.sum(PrintJob.print_duration).label("print_time"),
    ).filter(
        PrintJob.start_time >= start_date,
        PrintJob.start_time <= end_date,
    ).group_by(
        func.date(PrintJob.start_time)
    ).order_by(
        func.date(PrintJob.start_time)
    ).all()

    return [
        {
            "date": str(r.date),
            "job_count": r.total,
            "successful": r.successful or 0,
            "failed": r.failed or 0,
            "print_time": r.print_time or 0.0,
        }
        for r in results
    ]
```

#### 3. Analytics Routes
**File**: `src/api/routes/analytics.py`
**Changes**: Implement analytics endpoints

```python
"""
Analytics endpoints for 3D Print Logger.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.auth import get_api_key
from src.api.schemas import (
    AggregateStatsResponse,
    FilamentUsageResponse,
    PrinterStatsResponse,
    TimelineDataPoint,
    TimelineResponse,
)
from src.database.crud import (
    get_aggregate_stats,
    get_filament_usage_breakdown,
    get_job_stats_by_printer,
    get_jobs_timeline,
)
from src.database.engine import get_db
from src.database.models import ApiKey

router = APIRouter()


@router.get("/summary", response_model=AggregateStatsResponse)
async def get_summary(
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> AggregateStatsResponse:
    """Get aggregate statistics across all printers."""
    stats = get_aggregate_stats(db)
    return AggregateStatsResponse(**stats)


@router.get("/printers/{printer_id}", response_model=PrinterStatsResponse)
async def get_printer_stats(
    printer_id: int,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> PrinterStatsResponse:
    """Get statistics for a specific printer."""
    stats = get_job_stats_by_printer(db, printer_id)
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer with ID {printer_id} not found",
        )
    return PrinterStatsResponse(**stats)


@router.get("/filament", response_model=List[FilamentUsageResponse])
async def get_filament_usage(
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> List[FilamentUsageResponse]:
    """Get filament usage breakdown by type."""
    usage = get_filament_usage_breakdown(db)
    return [FilamentUsageResponse(**u) for u in usage]


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> TimelineResponse:
    """Get job timeline data for charts."""
    timeline = get_jobs_timeline(db, days=days)
    return TimelineResponse(
        period="daily",
        data=[TimelineDataPoint(**d) for d in timeline],
    )
```

### Success Criteria

#### Automated Verification
- [ ] Tests pass: `uv run pytest tests/test_api/test_analytics.py -v`
- [ ] Tests pass: `uv run pytest tests/test_database/test_crud.py -v` (new analytics queries)
- [ ] Type checking passes: `uv run mypy src/api/routes/analytics.py`

#### Manual Verification
- [ ] GET /api/analytics/summary returns aggregate stats
- [ ] GET /api/analytics/printers/{id} returns printer stats
- [ ] GET /api/analytics/filament returns filament breakdown
- [ ] GET /api/analytics/timeline returns chart data

**Implementation Note**: After completing this phase and all automated verification passes, pause for manual confirmation before proceeding.

---

## Phase 3.5: Admin Endpoints

### Overview
Implement admin endpoints for API key management and system health.

### Changes Required

#### 1. Admin Schemas
**File**: `src/api/schemas.py` (APPEND)
**Changes**: Add admin request/response schemas

```python
# ========== Admin Schemas ==========

class ApiKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(..., min_length=1, max_length=100)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class ApiKeyResponse(BaseSchema):
    """Schema for API key response (without full key)."""
    id: int
    key_prefix: str
    name: str
    is_active: bool
    last_used: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Schema for newly created API key (includes full key once)."""
    key: str  # Only shown once on creation


class SystemHealthResponse(BaseSchema):
    """Schema for system health status."""
    status: str  # healthy, degraded, unhealthy
    database: str
    moonraker_connections: int
    active_printers: int
    uptime_seconds: float
```

#### 2. Admin CRUD Operations
**File**: `src/database/crud.py` (APPEND)
**Changes**: Add admin operations

```python
# ========== Admin Operations ==========

import secrets

def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key with prefix and hash.

    Returns:
        Tuple of (full_key, key_prefix, key_hash)
    """
    # Generate 32 random bytes = 64 hex chars
    raw_key = secrets.token_hex(32)
    full_key = f"3dp_{raw_key}"
    key_prefix = f"3dp_{raw_key[:8]}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    return full_key, key_prefix, key_hash


def get_all_api_keys(db: Session) -> List[ApiKey]:
    """
    Get all API keys (for admin listing).

    Args:
        db: Database session

    Returns:
        List of all API keys
    """
    return db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()


def deactivate_api_key(db: Session, api_key_id: int) -> bool:
    """
    Deactivate an API key (soft delete).

    Args:
        db: Database session
        api_key_id: API key ID to deactivate

    Returns:
        True if deactivated, False if not found
    """
    api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
    if api_key is None:
        return False

    api_key.is_active = False
    db.commit()
    return True


def delete_api_key(db: Session, api_key_id: int) -> bool:
    """
    Delete an API key permanently.

    Args:
        db: Database session
        api_key_id: API key ID to delete

    Returns:
        True if deleted, False if not found
    """
    api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
    if api_key is None:
        return False

    db.delete(api_key)
    db.commit()
    return True
```

Note: Add `import hashlib` at top of crud.py.

#### 3. Admin Routes
**File**: `src/api/routes/admin.py`
**Changes**: Implement admin endpoints

```python
"""
Admin endpoints for 3D Print Logger.
"""

import time
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.auth import get_api_key
from src.api.schemas import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    SystemHealthResponse,
)
from src.database.crud import (
    create_api_key,
    deactivate_api_key,
    delete_api_key,
    generate_api_key,
    get_active_printers,
    get_all_api_keys,
)
from src.database.engine import get_db
from src.database.models import ApiKey
from src.moonraker.manager import MoonrakerManager

router = APIRouter()

# Track application start time for uptime
_app_start_time = time.time()


@router.post("/keys", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_new_api_key(
    key_data: ApiKeyCreate,
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> ApiKeyCreatedResponse:
    """
    Create a new API key.

    The full key is only shown once in this response.
    Store it securely - it cannot be retrieved again.
    """
    # Generate key components
    full_key, key_prefix, key_hash = generate_api_key()

    # Calculate expiration if specified
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)

    # Create in database
    api_key = create_api_key(
        db,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        expires_at=expires_at,
    )

    return ApiKeyCreatedResponse(
        id=api_key.id,
        key=full_key,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        is_active=api_key.is_active,
        last_used=api_key.last_used,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
    )


@router.get("/keys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> List[ApiKeyResponse]:
    """List all API keys (shows prefix only, not full key)."""
    keys = get_all_api_keys(db)
    return keys


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    permanent: bool = False,
    db: Session = Depends(get_db),
    current_key: ApiKey = Depends(get_api_key),
) -> None:
    """
    Revoke an API key.

    By default, deactivates the key (soft delete).
    Set permanent=true to permanently delete.

    Cannot revoke the key currently being used.
    """
    if key_id == current_key.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke the API key currently in use",
        )

    if permanent:
        deleted = delete_api_key(db, key_id)
    else:
        deleted = deactivate_api_key(db, key_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID {key_id} not found",
        )


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    db: Session = Depends(get_db),
    _api_key: ApiKey = Depends(get_api_key),
) -> SystemHealthResponse:
    """Get system health status."""
    # Check database
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # Check Moonraker connections
    manager = MoonrakerManager.get_instance()
    connection_count = len(manager.clients)

    # Get active printer count
    active_printers = len(get_active_printers(db))

    # Calculate uptime
    uptime = time.time() - _app_start_time

    # Determine overall status
    if db_status == "unhealthy":
        overall_status = "unhealthy"
    elif connection_count < active_printers:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return SystemHealthResponse(
        status=overall_status,
        database=db_status,
        moonraker_connections=connection_count,
        active_printers=active_printers,
        uptime_seconds=uptime,
    )
```

### Success Criteria

#### Automated Verification
- [ ] Tests pass: `uv run pytest tests/test_api/test_admin.py -v`
- [ ] Tests pass: `uv run pytest tests/test_database/test_crud.py -v` (new admin operations)
- [ ] Type checking passes: `uv run mypy src/api/routes/admin.py`

#### Manual Verification
- [ ] POST /api/admin/keys creates new key (shows full key once)
- [ ] GET /api/admin/keys lists keys (prefix only)
- [ ] DELETE /api/admin/keys/{id} revokes key
- [ ] GET /api/admin/health returns system status

**Implementation Note**: After completing this phase and all automated verification passes, pause for manual confirmation before proceeding.

---

## Phase 3.6: Test Suite & Documentation

### Overview
Create comprehensive test suite achieving 90%+ coverage.

### Changes Required

#### 1. Test Fixtures
**File**: `tests/conftest.py` (UPDATE)
**Changes**: Add API test fixtures

```python
# Add to existing conftest.py

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app
from src.api.auth import hash_api_key
from src.database.crud import create_api_key


@pytest.fixture
def client(db_session):
    """Create test client with database session override."""
    from src.database.engine import get_db

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def test_api_key(db_session) -> str:
    """Create a test API key and return the full key."""
    full_key = "3dp_test1234567890abcdef1234567890abcdef1234567890abcdef1234"
    key_hash = hash_api_key(full_key)
    key_prefix = full_key[:12]

    create_api_key(
        db_session,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name="Test API Key",
    )

    return full_key


@pytest.fixture
def auth_headers(test_api_key) -> dict:
    """Return headers with valid API key."""
    return {"X-API-Key": test_api_key}
```

#### 2. Test Files Structure
**Directory**: `tests/test_api/`

```
tests/test_api/
├── __init__.py
├── conftest.py          # API-specific fixtures
├── test_auth.py         # Authentication tests
├── test_main.py         # App lifecycle tests
├── test_printers.py     # Printer endpoint tests
├── test_jobs.py         # Job endpoint tests
├── test_analytics.py    # Analytics endpoint tests
└── test_admin.py        # Admin endpoint tests
```

#### 3. Example Test File
**File**: `tests/test_api/test_auth.py`

```python
"""Tests for API authentication."""

import pytest
from fastapi import status


class TestApiKeyAuth:
    """Test API key authentication."""

    def test_missing_api_key_returns_401(self, client):
        """Request without API key should return 401."""
        response = client.get("/api/printers")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing API key" in response.json()["detail"]

    def test_invalid_api_key_returns_401(self, client):
        """Request with invalid API key should return 401."""
        response = client.get(
            "/api/printers",
            headers={"X-API-Key": "invalid_key"}
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
        from datetime import datetime, timedelta
        from src.api.auth import hash_api_key
        from src.database.crud import create_api_key

        # Create expired key
        full_key = "3dp_expired123456789012345678901234567890123456789012345"
        key_hash = hash_api_key(full_key)
        create_api_key(
            db_session,
            key_hash=key_hash,
            key_prefix=full_key[:12],
            name="Expired Key",
            expires_at=datetime.utcnow() - timedelta(days=1),
        )

        response = client.get(
            "/api/printers",
            headers={"X-API-Key": full_key}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in response.json()["detail"].lower()
```

### Success Criteria

#### Automated Verification
- [ ] All API tests pass: `uv run pytest tests/test_api/ -v`
- [ ] Coverage > 90%: `uv run pytest tests/ -v --cov=src --cov-fail-under=90`
- [ ] Type checking passes: `uv run mypy src/`
- [ ] Linting passes: `uv run ruff check src/`

#### Manual Verification
- [ ] Full API workflow tested manually
- [ ] OpenAPI documentation complete at `/docs`
- [ ] Error responses are consistent and informative

---

## Testing Strategy

### Unit Tests
- Test each CRUD operation independently
- Test schema validation (valid/invalid inputs)
- Test authentication logic (missing, invalid, expired keys)

### Integration Tests
- Test endpoint behavior with database
- Test pagination and filtering combinations
- Test error responses (404, 409, 422)

### Key Edge Cases
- Empty database (no printers, no jobs)
- Pagination boundaries (offset beyond total)
- Filter combinations (printer_id + status + date range)
- Concurrent API key usage tracking
- Unicode in printer names/filenames

### Test Coverage Target
- Minimum: 90% code coverage
- Focus: All error paths tested
- Mock: MoonrakerManager for printer status tests

---

## Performance Considerations

### Database Queries
- Use indexes on frequently filtered columns (already defined in models)
- Paginate large result sets (limit/offset)
- Use count() optimization for pagination total

### Connection Management
- Database sessions via dependency injection (auto-cleanup)
- MoonrakerManager singleton pattern for connection reuse

### Future Optimizations (Not in MVP)
- Redis caching for analytics queries
- Background task for slow operations
- Connection pooling configuration

---

## Migration Notes

### First-Time Setup
1. Run database initialization: `uv run python -c "from src.database.engine import init_database; init_database()"`
2. Create first API key via CLI or temporary endpoint
3. Use key for all subsequent API calls

### Initial API Key Creation
Since API key is required for admin endpoints, provide CLI command:

**File**: `src/cli.py` (NEW)

```python
"""CLI utilities for 3D Print Logger."""

import click
from src.database.engine import get_session_local, init_database
from src.database.crud import create_api_key, generate_api_key


@click.group()
def cli():
    """3D Print Logger CLI."""
    pass


@cli.command()
@click.option("--name", default="Initial Admin Key", help="Name for the API key")
def create_initial_key(name: str):
    """Create the initial API key for bootstrapping."""
    init_database()

    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        full_key, key_prefix, key_hash = generate_api_key()
        api_key = create_api_key(
            db,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
        )

        click.echo(f"API Key created successfully!")
        click.echo(f"Name: {api_key.name}")
        click.echo(f"Key: {full_key}")
        click.echo("")
        click.echo("IMPORTANT: Save this key securely. It cannot be retrieved again.")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
```

Usage: `uv run python -m src.cli create-initial-key --name "My API Key"`

---

## References

- Original architecture: `thoughts/shared/plans/architecture-design.md`
- Continuity ledger: `thoughts/ledgers/CONTINUITY_CLAUDE-3d-print-logger.md`
- Database models: `src/database/models.py`
- CRUD operations: `src/database/crud.py`
- Moonraker manager: `src/moonraker/manager.py`
- FastAPI security docs: https://fastapi.tiangolo.com/tutorial/security/
- Pydantic v2 docs: https://docs.pydantic.dev/latest/

---

## Estimated Complexity

| Phase | Effort | Risk | Notes |
|-------|--------|------|-------|
| 3.1 Core Setup | Low | Low | Straightforward FastAPI setup |
| 3.2 Printers | Medium | Low | Standard CRUD with status integration |
| 3.3 Jobs | Medium | Low | Pagination adds complexity |
| 3.4 Analytics | Medium | Medium | Query complexity |
| 3.5 Admin | Low | Low | Simple key management |
| 3.6 Tests | High | Low | Time-consuming but low risk |

**Total estimated time**: 2-3 days for complete implementation with tests
