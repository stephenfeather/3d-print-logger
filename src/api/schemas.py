"""
Pydantic schemas for API request/response models.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Generic type for paginated responses
T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(from_attributes=True)


# ========== Pagination ==========


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    limit: int = Field(
        default=20, ge=1, le=100, description="Number of items per page"
    )
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


# ========== Printer Schemas ==========


class PrinterCreate(BaseModel):
    """Schema for creating a new printer."""

    name: str = Field(..., min_length=1, max_length=100, description="Printer name")
    moonraker_url: str = Field(..., description="Moonraker API URL")
    location: Optional[str] = Field(
        None, max_length=200, description="Physical location"
    )
    moonraker_api_key: Optional[str] = Field(
        None, description="Moonraker API key if required"
    )

    # Printer hardware details (Issue #8)
    printer_type: Optional[Literal["FDM", "Resin", "SLS"]] = Field(
        None, description="Type of 3D printer"
    )
    make: Optional[str] = Field(None, max_length=100, description="Manufacturer")
    model: Optional[str] = Field(None, max_length=100, description="Model name")
    description: Optional[str] = Field(None, max_length=500, description="Description")

    # Printer specifications
    filament_diameter: Optional[Literal[1.75, 2.85, 3.0]] = Field(
        1.75, description="Filament diameter in mm"
    )
    nozzle_diameter: Optional[float] = Field(
        None, gt=0, description="Nozzle diameter in mm"
    )
    bed_x: Optional[float] = Field(None, gt=0, description="Bed width in mm")
    bed_y: Optional[float] = Field(None, gt=0, description="Bed depth in mm")
    bed_z: Optional[float] = Field(None, gt=0, description="Bed height in mm")
    has_heated_bed: bool = Field(False, description="Has heated bed")
    has_heated_chamber: bool = Field(False, description="Has heated chamber")

    # Material tracking (Spoolman integration future)
    loaded_materials: Optional[List[Dict[str, Any]]] = Field(
        None, description="Currently loaded materials"
    )


class PrinterUpdate(BaseModel):
    """Schema for updating a printer. All fields optional."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    moonraker_url: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    moonraker_api_key: Optional[str] = None
    is_active: Optional[bool] = None

    # Printer hardware details (Issue #8)
    printer_type: Optional[Literal["FDM", "Resin", "SLS"]] = None
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    # Printer specifications
    filament_diameter: Optional[Literal[1.75, 2.85, 3.0]] = None
    nozzle_diameter: Optional[float] = Field(None, gt=0)
    bed_x: Optional[float] = Field(None, gt=0)
    bed_y: Optional[float] = Field(None, gt=0)
    bed_z: Optional[float] = Field(None, gt=0)
    has_heated_bed: Optional[bool] = None
    has_heated_chamber: Optional[bool] = None

    # Material tracking
    loaded_materials: Optional[List[Dict[str, Any]]] = None


class PrinterResponse(BaseSchema):
    """Schema for printer response."""

    id: int
    name: str
    moonraker_url: str
    location: Optional[str] = None
    is_active: bool
    last_seen: Optional[datetime] = None

    # Printer hardware details (Issue #8)
    printer_type: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    description: Optional[str] = None

    # Printer specifications
    filament_diameter: Optional[float] = None
    nozzle_diameter: Optional[float] = None
    bed_x: Optional[float] = None
    bed_y: Optional[float] = None
    bed_z: Optional[float] = None
    has_heated_bed: bool = False
    has_heated_chamber: bool = False

    # Material tracking
    loaded_materials: Optional[List[Dict[str, Any]]] = None

    created_at: datetime
    updated_at: datetime


class PrinterStatusResponse(BaseModel):
    """Schema for printer status response."""

    printer_id: int
    name: str
    is_connected: bool
    state: Optional[str] = None
    progress: Optional[float] = None
    current_file: Optional[str] = None
    error: Optional[str] = None


# ========== Job Schemas ==========


class JobDetailsResponse(BaseSchema):
    """Schema for job details (parsed gcode metadata)."""

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
    thumbnail_base64: Optional[str] = None

    # Slicer information (Issue #5)
    slicer_name: Optional[str] = None
    slicer_version: Optional[str] = None

    # Multi-filament usage and cost (Issue #5)
    filament_used_mm: Optional[List[float]] = None
    filament_used_cm3: Optional[List[float]] = None
    filament_used_g: Optional[List[float]] = None
    filament_cost: Optional[List[float]] = None
    total_filament_used_g: Optional[float] = None
    total_filament_cost: Optional[float] = None

    # Config block (Issue #5)
    config_block: Optional[Dict[str, str]] = None


class JobResponse(BaseSchema):
    """Schema for job response."""

    id: int
    printer_id: int
    job_id: str
    user: Optional[str] = None
    filename: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    print_duration: Optional[float] = None
    total_duration: Optional[float] = None
    filament_used: Optional[float] = None
    job_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    details: Optional[JobDetailsResponse] = None


class JobListFilter(BaseModel):
    """Query parameters for filtering jobs."""

    printer_id: Optional[int] = None
    status: Optional[str] = None
    start_after: Optional[datetime] = None
    start_before: Optional[datetime] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# ========== Analytics Schemas ==========


class DashboardSummary(BaseModel):
    """Dashboard summary statistics."""

    total_jobs: int = 0
    total_print_time: float = 0.0
    total_filament_used: float = 0.0
    successful_jobs: int = 0
    failed_jobs: int = 0
    active_printers: int = 0


class PrinterStats(BaseModel):
    """Per-printer statistics."""

    printer_id: int
    printer_name: str
    total_jobs: int = 0
    total_print_time: float = 0.0
    total_filament_used: float = 0.0
    successful_jobs: int = 0
    failed_jobs: int = 0
    last_job_at: Optional[datetime] = None


class FilamentUsage(BaseModel):
    """Filament usage by type."""

    filament_type: str
    total_used: float = 0.0
    job_count: int = 0


class TimelineEntry(BaseModel):
    """Timeline data point."""

    period: str  # Date string (YYYY-MM-DD, YYYY-WW, or YYYY-MM)
    job_count: int = 0
    total_print_time: float = 0.0
    successful_jobs: int = 0
    failed_jobs: int = 0


# ========== Admin Schemas ==========


class ApiKeyCreate(BaseModel):
    """Schema for creating a new API key."""

    name: str = Field(..., min_length=1, max_length=100)
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    """Schema for API key response (without sensitive data)."""

    id: int
    key_prefix: str
    name: str
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    created_at: datetime


class ApiKeyCreated(ApiKeyResponse):
    """Schema for newly created API key (includes full key)."""

    key: str  # Full key returned only on creation


class SystemInfo(BaseModel):
    """System information response."""

    version: str
    database_type: str
    active_printers: int
    total_jobs: int
    uptime_seconds: Optional[float] = None


# ========== Maintenance Schemas (Issue #9) ==========


class MaintenanceCreate(BaseModel):
    """Schema for creating a maintenance record."""

    printer_id: int = Field(..., description="ID of the printer")
    date: datetime = Field(..., description="When maintenance was performed")
    category: str = Field(
        ..., min_length=1, max_length=100, description="Category of maintenance"
    )
    description: str = Field(
        ..., min_length=1, max_length=500, description="What was done"
    )
    done: bool = Field(default=False, description="Whether maintenance is completed")
    cost: Optional[float] = Field(None, ge=0, description="Cost of maintenance")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")


class MaintenanceUpdate(BaseModel):
    """Schema for updating a maintenance record."""

    date: Optional[datetime] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    done: Optional[bool] = None
    cost: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=2000)


class MaintenanceResponse(BaseSchema):
    """Schema for maintenance record response."""

    id: int
    printer_id: int
    date: datetime
    done: bool
    category: str
    description: str
    cost: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
