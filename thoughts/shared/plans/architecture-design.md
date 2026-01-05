# 3D Print Logger - Architecture & Database Design

**Created**: 2026-01-03
**Status**: Design phase - ready for review

## Overview

Self-hosted application for logging and analyzing 3D print jobs from multiple Klipper/Moonraker printers.

### Design Principles
- **Multi-printer first**: Support multiple printers from day 1
- **Database abstraction**: SQLite for simple deployments, MySQL 8 for production
- **Real-time updates**: WebSocket subscriptions to Moonraker instances
- **Extensibility**: Prepare for future integrations (Spoolman, ESP32 sensors)
- **Self-hosted**: Run on local hardware (RPi, NAS, home server)

---

## Database Schema

### Table: `printers`
Tracks each printer instance and its Moonraker connection details.

```sql
CREATE TABLE printers (
    id                  INTEGER PRIMARY KEY AUTO_INCREMENT,  -- MySQL syntax; SQLite uses AUTOINCREMENT
    name                VARCHAR(100) NOT NULL,               -- User-friendly name
    location            VARCHAR(200),                        -- Physical location
    moonraker_url       VARCHAR(500) NOT NULL,               -- http://printer.local:7125
    moonraker_api_key   VARCHAR(200),                        -- If Moonraker requires auth
    is_active           BOOLEAN DEFAULT TRUE,                -- Enable/disable monitoring
    last_seen           TIMESTAMP,                           -- Last successful connection
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE(name),
    INDEX idx_active (is_active)
);
```

**Notes:**
- `moonraker_url`: Full URL including port (default 7125)
- `is_active`: Allows temporarily disabling a printer without deletion
- `last_seen`: Updated on each successful WebSocket connection/message

---

### Table: `print_jobs`
Core job tracking based on Moonraker's job_history schema.

```sql
CREATE TABLE print_jobs (
    id                  INTEGER PRIMARY KEY AUTO_INCREMENT,
    printer_id          INTEGER NOT NULL,                    -- FK to printers
    job_id              VARCHAR(100) NOT NULL,               -- Moonraker's job_id (UUID)
    user                VARCHAR(100),                        -- Klippy username (often "default")
    filename            VARCHAR(500) NOT NULL,               -- Gcode filename
    status              VARCHAR(50) NOT NULL,                -- completed, error, cancelled
    start_time          TIMESTAMP NOT NULL,
    end_time            TIMESTAMP,
    print_duration      FLOAT,                               -- Seconds of actual printing
    total_duration      FLOAT,                               -- Seconds including pauses
    filament_used       FLOAT,                               -- Millimeters
    metadata            JSON,                                -- Moonraker's metadata (slicer, object height, etc.)
    auxiliary_data      JSON,                                -- Additional tracking data
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    UNIQUE (printer_id, job_id),                             -- Prevent duplicates per printer
    INDEX idx_printer_status (printer_id, status),
    INDEX idx_start_time (start_time),
    INDEX idx_status (status)
);
```

**Status values:**
- `printing`: Currently in progress
- `paused`: Print paused
- `completed`: Successfully finished
- `error`: Print failed
- `cancelled`: User cancelled

**Notes:**
- `job_id`: Moonraker generates UUIDs per print job
- `printer_id + job_id` composite unique key handles multi-printer job_id collisions
- `metadata` (JSON): Stores Moonraker's native metadata (slicer info, estimated time, etc.)
- Durations in seconds (float for sub-second precision)
- Filament in millimeters (convert to grams via density in UI)

---

### Table: `job_details`
Extended metadata from OrcaSlicer gcode files.

```sql
CREATE TABLE job_details (
    id                  INTEGER PRIMARY KEY AUTO_INCREMENT,
    print_job_id        INTEGER NOT NULL,                    -- FK to print_jobs

    -- Slicer settings (extracted from gcode comments)
    layer_height        FLOAT,                               -- mm
    first_layer_height  FLOAT,                               -- mm
    nozzle_temp         INTEGER,                             -- °C
    bed_temp            INTEGER,                             -- °C
    print_speed         INTEGER,                             -- mm/s
    infill_percentage   INTEGER,                             -- %
    infill_pattern      VARCHAR(50),                         -- grid, honeycomb, etc.
    support_enabled     BOOLEAN,
    support_type        VARCHAR(50),                         -- normal, tree, etc.
    filament_type       VARCHAR(50),                         -- PLA, PETG, ABS, etc.
    filament_brand      VARCHAR(100),
    filament_color      VARCHAR(50),

    -- Print statistics
    estimated_time      INTEGER,                             -- Seconds (from slicer)
    estimated_filament  FLOAT,                               -- Grams (from slicer)
    layer_count         INTEGER,
    object_height       FLOAT,                               -- mm

    -- Raw gcode metadata (full extraction)
    raw_metadata        JSON,                                -- All parsed gcode comments

    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (print_job_id) REFERENCES print_jobs(id) ON DELETE CASCADE,
    UNIQUE (print_job_id),                                   -- One detail record per job
    INDEX idx_filament_type (filament_type),
    INDEX idx_layer_height (layer_height)
);
```

**Notes:**
- **Blocked on sample gcode file**: Field list may expand based on OrcaSlicer's actual metadata
- `raw_metadata` (JSON): Stores complete parsed metadata for future analysis
- Nullable fields: Not all gcode files will have all metadata
- Temperatures stored as integers (sufficient for 3D printing)

---

### Table: `job_totals`
Aggregated statistics per printer (similar to Moonraker's totals table).

```sql
CREATE TABLE job_totals (
    id                  INTEGER PRIMARY KEY AUTO_INCREMENT,
    printer_id          INTEGER NOT NULL,                    -- FK to printers

    total_jobs          INTEGER DEFAULT 0,
    total_time          FLOAT DEFAULT 0,                     -- Seconds of print time
    total_print_time    FLOAT DEFAULT 0,                     -- Seconds excluding pauses
    total_filament_used FLOAT DEFAULT 0,                     -- Millimeters
    longest_job         FLOAT DEFAULT 0,                     -- Seconds

    last_updated        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    UNIQUE (printer_id)                                      -- One totals row per printer
);
```

**Update strategy:**
- Increment on job completion
- Use database triggers or application-level updates
- Consider separate totals for successful vs. failed jobs in future

---

### Table: `api_keys`
API key management for authentication.

```sql
CREATE TABLE api_keys (
    id                  INTEGER PRIMARY KEY AUTO_INCREMENT,
    key_hash            VARCHAR(64) NOT NULL,                -- SHA-256 hash of API key
    key_prefix          VARCHAR(10) NOT NULL,                -- First 8 chars for identification
    name                VARCHAR(100) NOT NULL,               -- User-friendly name
    is_active           BOOLEAN DEFAULT TRUE,
    last_used           TIMESTAMP,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at          TIMESTAMP,                           -- Optional expiration

    UNIQUE (key_hash),
    INDEX idx_active (is_active)
);
```

**Notes:**
- Store only hashed keys (never plaintext)
- `key_prefix`: Show user "3dp_12345678..." for identification
- Single-user design: All keys have same permissions
- Future: Add scopes/permissions if multi-user needed

---

### Database Compatibility Notes

**SQLite vs MySQL 8 differences:**

| Feature | SQLite | MySQL 8 |
|---------|--------|---------|
| Auto-increment | `INTEGER PRIMARY KEY AUTOINCREMENT` | `AUTO_INCREMENT` |
| Boolean | `INTEGER` (0/1) | `BOOLEAN` |
| Timestamp | `TEXT` or `INTEGER` | `TIMESTAMP` |
| JSON | Native JSON1 extension | Native JSON type |
| ON UPDATE | Not supported | `ON UPDATE CURRENT_TIMESTAMP` |

**SQLAlchemy Abstraction Strategy:**
- Use SQLAlchemy ORM types that map correctly to both databases
- `Boolean` → SQLAlchemy handles 0/1 for SQLite
- `DateTime` → SQLAlchemy handles timestamp formats
- `JSON` → SQLAlchemy's JSON type works with both
- Handle `ON UPDATE` via ORM `onupdate` parameter

---

## Application Architecture

### Directory Structure

```
3d-print-logger/
├── src/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── engine.py              # Database engine setup
│   │   └── migrations/            # Alembic migrations
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py                # API key middleware
│   │   ├── routes/
│   │   │   ├── printers.py        # Printer CRUD endpoints
│   │   │   ├── jobs.py            # Job query endpoints
│   │   │   ├── analytics.py      # Dashboard analytics
│   │   │   └── admin.py           # API key management
│   ├── moonraker/
│   │   ├── __init__.py
│   │   ├── client.py              # WebSocket client per printer
│   │   ├── manager.py             # Multi-printer connection manager
│   │   └── handlers.py            # Event handlers (job updates)
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── orcaslicer.py          # Gcode metadata extraction
│   └── utils/
│       ├── __init__.py
│       └── crypto.py              # API key generation/hashing
├── frontend/                      # Vue.js app (future)
├── tests/
│   ├── test_database/
│   ├── test_api/
│   ├── test_moonraker/
│   └── test_parsers/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config.example.yml             # Example configuration
├── requirements.txt               # Python dependencies
└── README.md
```

---

### Component Design

#### 1. FastAPI Application (`src/main.py`)

```python
from fastapi import FastAPI
from src.api.auth import api_key_middleware
from src.api.routes import printers, jobs, analytics, admin
from src.moonraker.manager import MoonrakerManager
from src.database.engine import init_database

app = FastAPI(title="3D Print Logger")

# Middleware
app.middleware("http")(api_key_middleware)

# Routes
app.include_router(printers.router, prefix="/api/printers", tags=["printers"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Lifecycle
@app.on_event("startup")
async def startup():
    await init_database()
    manager = MoonrakerManager.get_instance()
    await manager.start()

@app.on_event("shutdown")
async def shutdown():
    manager = MoonrakerManager.get_instance()
    await manager.stop()
```

---

#### 2. Moonraker Connection Manager (`src/moonraker/manager.py`)

**Design pattern**: Singleton manager with per-printer WebSocket clients

**Responsibilities:**
- Load printer configurations from database
- Spawn WebSocket client per active printer
- Handle reconnection logic
- Route events to handlers
- Monitor printer health (last_seen updates)

**Architecture:**

```python
class MoonrakerManager:
    """
    Manages WebSocket connections to multiple Moonraker instances.
    Singleton pattern ensures single manager per application.
    """

    _instance = None

    def __init__(self):
        self.clients: Dict[int, MoonrakerClient] = {}  # printer_id -> client
        self.reconnect_tasks: Dict[int, asyncio.Task] = {}

    async def start(self):
        """Load printers from DB and start connections."""
        printers = await get_active_printers()
        for printer in printers:
            await self.connect_printer(printer)

    async def connect_printer(self, printer: Printer):
        """Start WebSocket client for a printer."""
        client = MoonrakerClient(
            printer_id=printer.id,
            url=printer.moonraker_url,
            api_key=printer.moonraker_api_key,
            event_handler=self.handle_event
        )
        self.clients[printer.id] = client
        await client.connect()

    async def handle_event(self, printer_id: int, event: dict):
        """Route events to appropriate handlers."""
        event_type = event.get("method")

        if event_type == "notify_status_update":
            await handle_status_update(printer_id, event["params"])
        elif event_type == "notify_history_changed":
            await handle_history_changed(printer_id, event["params"])
```

**Reconnection strategy:**
- Exponential backoff: 5s, 10s, 30s, 60s (max)
- Update `printers.last_seen` on successful connection
- Log connection failures for monitoring

---

#### 3. Moonraker WebSocket Client (`src/moonraker/client.py`)

**Per-printer WebSocket client:**

```python
class MoonrakerClient:
    """WebSocket client for single Moonraker instance."""

    def __init__(self, printer_id, url, api_key, event_handler):
        self.printer_id = printer_id
        self.ws_url = f"{url.replace('http', 'ws')}/websocket"
        self.api_key = api_key
        self.event_handler = event_handler
        self.ws = None
        self.running = False

    async def connect(self):
        """Establish WebSocket connection and subscribe to events."""
        self.ws = await websockets.connect(self.ws_url)

        # Subscribe to print_stats for status updates
        await self.subscribe("print_stats")

        # Subscribe to history notifications
        await self.subscribe("notify_history_changed")

        # Start listen loop
        self.running = True
        asyncio.create_task(self.listen())

    async def listen(self):
        """Receive and route WebSocket messages."""
        while self.running:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                await self.event_handler(self.printer_id, data)
            except Exception as e:
                logger.error(f"Printer {self.printer_id} error: {e}")
                await self.reconnect()

    async def subscribe(self, object_name: str):
        """Subscribe to Moonraker object updates."""
        request = {
            "jsonrpc": "2.0",
            "method": "printer.objects.subscribe",
            "params": {"objects": {object_name: None}},
            "id": random.randint(1, 10000)
        }
        await self.ws.send(json.dumps(request))
```

---

#### 4. Event Handlers (`src/moonraker/handlers.py`)

**Job lifecycle tracking:**

```python
async def handle_status_update(printer_id: int, params: dict):
    """
    Handle print_stats updates.
    Tracks: state, progress, filename, print_duration, filament_used
    """
    stats = params.get("print_stats", {})
    state = stats.get("state")  # standby, printing, paused, complete, error

    if state == "printing":
        # Create or update active job
        await upsert_active_job(printer_id, stats)

    elif state in ["complete", "error", "cancelled"]:
        # Finalize job and update totals
        await finalize_job(printer_id, stats)
        await update_job_totals(printer_id)

async def handle_history_changed(printer_id: int, params: dict):
    """
    Handle history notifications from Moonraker.
    Moonraker maintains its own job_history - we can query and sync.
    """
    action = params.get("action")  # added, finished, deleted

    if action == "finished":
        job = params.get("job")
        await sync_job_from_moonraker(printer_id, job)
```

---

#### 5. Gcode Metadata Parser (`src/parsers/orcaslicer.py`)

**Design** (pending sample gcode file):

```python
class OrcaSlicerParser:
    """
    Extract metadata from OrcaSlicer gcode file headers.

    OrcaSlicer embeds settings as comments in format:
    ; layer_height = 0.2
    ; filament_type = PLA
    ; etc.
    """

    def parse_file(self, filepath: str) -> dict:
        """
        Parse gcode file and extract metadata.
        Returns dict with standardized keys.
        """
        metadata = {}

        with open(filepath, 'r') as f:
            # Read header (first ~100 lines typically contain metadata)
            for i, line in enumerate(f):
                if i > 200:  # Stop after header section
                    break

                if line.startswith(';'):
                    # Parse comment line
                    # Example: "; layer_height = 0.2"
                    parsed = self._parse_comment(line)
                    if parsed:
                        metadata.update(parsed)

        return self._normalize_metadata(metadata)

    def _parse_comment(self, line: str) -> dict | None:
        """Extract key-value from comment line."""
        # Implementation TBD based on sample file
        pass

    def _normalize_metadata(self, raw: dict) -> dict:
        """
        Convert raw metadata to job_details schema.
        Handle units, type conversions, etc.
        """
        return {
            "layer_height": float(raw.get("layer_height", 0)),
            "nozzle_temp": int(raw.get("nozzle_temperature_0", 0)),
            # ... etc
            "raw_metadata": raw  # Store everything for future use
        }
```

**Trigger point**: Parse metadata when job completes (or on gcode file upload if implementing upload feature)

---

#### 6. API Key Authentication (`src/api/auth.py`)

```python
from fastapi import Request, HTTPException
from src.utils.crypto import verify_api_key

async def api_key_middleware(request: Request, call_next):
    """
    Validate API key from Authorization header.
    Format: Authorization: Bearer 3dp_abc123...
    """

    # Skip auth for health check endpoint
    if request.url.path == "/health":
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing API key")

    api_key = auth_header.replace("Bearer ", "")

    if not await verify_api_key(api_key):
        raise HTTPException(401, "Invalid API key")

    return await call_next(request)
```

---

#### 7. Configuration (`config.yml`)

```yaml
database:
  type: sqlite  # or mysql
  # SQLite
  path: ./data/printlog.db
  # MySQL (if type: mysql)
  # host: localhost
  # port: 3306
  # user: printlog
  # password: secret
  # database: printlog

moonraker:
  reconnect_delay: 5  # seconds
  max_reconnect_delay: 60
  health_check_interval: 30

api:
  host: 0.0.0.0
  port: 8000
  cors_origins:
    - http://localhost:3000  # Frontend dev server

logging:
  level: INFO
  file: ./logs/printlog.log
```

---

### API Endpoints (REST)

#### Printers
- `GET /api/printers` - List all printers
- `POST /api/printers` - Add new printer
- `GET /api/printers/{id}` - Get printer details
- `PUT /api/printers/{id}` - Update printer
- `DELETE /api/printers/{id}` - Remove printer
- `GET /api/printers/{id}/status` - Current print status

#### Jobs
- `GET /api/jobs` - List jobs (filterable by printer, status, date range)
- `GET /api/jobs/{id}` - Get job details (includes job_details)
- `GET /api/jobs/{id}/details` - Get extended metadata
- `DELETE /api/jobs/{id}` - Delete job record

#### Analytics
- `GET /api/analytics/summary` - Overall stats (all printers)
- `GET /api/analytics/printers/{id}` - Per-printer stats
- `GET /api/analytics/filament` - Filament usage breakdown
- `GET /api/analytics/timeline` - Jobs over time (chart data)

#### Admin
- `POST /api/admin/keys` - Generate new API key
- `GET /api/admin/keys` - List API keys (shows prefix only)
- `DELETE /api/admin/keys/{id}` - Revoke API key

---

## Deployment Architecture

### Docker Container

**Services:**
1. **App**: FastAPI + Uvicorn
2. **Database**: SQLite (embedded) or MySQL (separate container)

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data  # SQLite database
      - ./logs:/app/logs
      - ./config.yml:/app/config.yml
    environment:
      - CONFIG_PATH=/app/config.yml
    restart: unless-stopped

  # Optional: MySQL for production
  db:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: printlog
      MYSQL_USER: printlog
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    restart: unless-stopped

volumes:
  mysql_data:
```

---

## Implementation Phases

### Phase 1: Database & Models
- [ ] SQLAlchemy models for all tables
- [ ] Alembic migrations for schema creation
- [ ] Database engine factory (SQLite/MySQL toggle)
- [ ] Basic CRUD operations

### Phase 2: Moonraker Integration
- [ ] WebSocket client implementation
- [ ] Connection manager (multi-printer)
- [ ] Event handlers for job tracking
- [ ] Reconnection logic with backoff

### Phase 3: API Layer
- [ ] FastAPI app structure
- [ ] API key authentication middleware
- [ ] Printer CRUD endpoints
- [ ] Job query endpoints
- [ ] Analytics endpoints

### Phase 4: Gcode Parser
- [ ] **BLOCKED**: Obtain sample OrcaSlicer gcode file
- [ ] Design parser based on actual metadata format
- [ ] Extract and normalize metadata
- [ ] Populate job_details table

### Phase 5: Frontend (Future)
- [ ] Vue.js dashboard
- [ ] Printer management UI
- [ ] Job history table with filters
- [ ] Analytics charts (Chart.js or similar)

### Phase 6: Deployment
- [ ] Dockerfile
- [ ] Docker Compose configuration
- [ ] Installation documentation
- [ ] Sample config files

---

## Open Design Questions

1. **Historical backfill**: When connecting to existing printer, should we:
   - Import Moonraker's historical jobs from its SQLite database?
   - Only track new jobs going forward?
   - Make it configurable?

2. **Gcode file storage**: Should we:
   - Store gcode files locally for re-parsing?
   - Only store extracted metadata?
   - Fetch from Moonraker on-demand?

3. **Job deduplication**: If Moonraker sends duplicate history events:
   - Trust `UNIQUE (printer_id, job_id)` constraint?
   - Implement idempotent upsert logic?

4. **Analytics caching**: For large datasets:
   - Pre-aggregate daily/weekly stats?
   - Calculate on-demand with query optimization?
   - Use materialized views (if MySQL)?

5. **Timezone handling**:
   - Store all timestamps in UTC?
   - Allow per-printer timezone configuration?
   - Handle client timezone in frontend only?

---

## Next Steps

1. **Review this design** with user
2. **Obtain sample OrcaSlicer gcode file** to finalize `job_details` schema
3. **Begin Phase 1**: Implement database models and migrations
4. **Set up project structure**: Create directory tree and dependencies

---

## References

- [Moonraker API Docs](https://moonraker.readthedocs.io/)
- [Moonraker WebSocket API](https://moonraker.readthedocs.io/en/latest/web_api/#websocket-apis)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
