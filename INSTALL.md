# Installation Guide

This guide covers deploying 3D Print Logger using Docker.

## Prerequisites

- Docker 20.10+ and Docker Compose v2+
- Network access to your Moonraker instances
- (Optional) MySQL 8 for production deployments

### macOS with Colima

On macOS, Docker can run inside a Colima VM:

```bash
# Install Colima (if not already installed)
brew install colima docker docker-compose

# Start Colima
colima start

# Verify Docker is working
docker info
```

Note: When using Colima, ensure the VM has network access to your Moonraker instances on your local network.

## Quick Start (SQLite)

The simplest deployment uses SQLite for storage:

```bash
# Clone the repository
git clone https://github.com/stephenfeather/3d-print-logger.git
cd 3d-print-logger

# Copy and configure settings
cp config.example.yml config.yml
cp .env.example .env

# Create data directories
mkdir -p data logs

# Build and start (with Docker Compose)
cd docker
docker compose up -d
```

**Alternative: Direct Docker commands** (if docker compose plugin is unavailable):

```bash
# Build the image from project root
docker build -f docker/Dockerfile -t 3d-print-logger .

# Run the container
docker run -d \
  --name print-logger \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config.yml:/app/config.yml:ro \
  3d-print-logger
```

The application will be available at `http://localhost:8000`.

## Configuration

### config.yml

Edit `config.yml` to configure your deployment:

```yaml
# Database Configuration
database:
  type: sqlite           # sqlite or mysql
  path: ./data/printlog.db  # SQLite file path

# API Server Settings
api:
  host: 0.0.0.0
  port: 8000
  cors_origins:
    - http://localhost:3000

# Moonraker Connection Settings
moonraker:
  reconnect_delay: 5
  max_reconnect_delay: 60
  health_check_interval: 30

# Logging
logging:
  level: INFO
  file: ./logs/printlog.log
```

### Environment Variables

Edit `.env` to customize ports:

```bash
APP_PORT=8000
```

## Initial Setup

After starting the container:

1. **Create an API key**: The application requires authentication. Create your first API key:

   ```bash
   # Access the container
   docker exec -it print-logger /bin/bash

   # Generate an API key (note: implement this command)
   # For now, use the API endpoint directly or the web UI
   ```

2. **Add your printers**: Navigate to the web UI at `http://localhost:8000` and add your Moonraker printer URLs.

3. **Verify connectivity**: Check that printers show as "online" in the dashboard.

## Production Deployment (MySQL)

For larger deployments or better performance, use MySQL:

1. Edit `docker/docker-compose.yml` and uncomment the `db` service and `volumes` section.

2. Update `.env` with MySQL credentials:

   **SECURITY WARNING**: Always use unique, strong passwords for production deployments!
   - Use different passwords for `DB_ROOT_PASSWORD` and `DB_PASSWORD`
   - Minimum 16 characters with mixed case, numbers, and symbols
   - Never reuse passwords from other systems
   - Consider using a password manager to generate and store credentials

   ```bash
   DB_ROOT_PASSWORD=your_secure_root_password
   DB_DATABASE=printlog
   DB_USER=printlog
   DB_PASSWORD=your_secure_password
   ```

3. Update `config.yml` to use MySQL:
   ```yaml
   database:
     type: mysql
     host: db
     port: 3306
     user: printlog
     password: your_secure_password
     database: printlog
   ```

4. Start the stack:
   ```bash
   cd docker
   docker compose up -d
   ```

## Updating

To update to a new version:

```bash
cd docker
docker compose down
git pull
docker compose build --no-cache
docker compose up -d
```

## Data Persistence

Data is stored in the following locations:

| Path | Contents |
|------|----------|
| `./data/` | SQLite database (if using SQLite) |
| `./logs/` | Application logs |
| `./config.yml` | Configuration file |

These directories are mounted as volumes, so your data persists across container restarts.

## Backup

### SQLite Backup

```bash
# Stop the container
docker compose down

# Backup the database
cp data/printlog.db data/printlog.db.backup

# Restart
docker compose up -d
```

### MySQL Backup

```bash
docker exec print-logger-db mysqldump -u printlog -p printlog > backup.sql
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker compose logs -f app
```

### Can't connect to Moonraker

1. Verify Moonraker is running on your printer
2. Check network connectivity between Docker host and printer
3. Ensure Moonraker allows connections from your Docker host IP
4. Check `trusted_clients` in Moonraker's `moonraker.conf`

### Database errors

For SQLite permission issues:
```bash
chmod 755 data/
chmod 644 data/printlog.db
```

### Health check failing

The container health check hits `/health`. If it's failing:
```bash
# Check if the app is responding
curl http://localhost:8000/health

# Check container logs
docker compose logs app
```

## Network Configuration

### Firewall

Ensure port 8000 (or your configured `APP_PORT`) is accessible.

### Reverse Proxy (nginx example)

```nginx
server {
    listen 80;
    server_name printlog.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Raspberry Pi Deployment

The Docker image supports ARM64. For Raspberry Pi 4 or newer:

```bash
# Same steps as Quick Start
cd docker
docker compose up -d
```

Note: Initial build may take 10-15 minutes on Raspberry Pi due to npm dependencies.

## Manual Installation (Without Docker)

If you prefer not to use Docker:

1. Install Python 3.10+ and Node.js 22+
2. Install dependencies:
   ```bash
   pip install -r requirements-prod.txt
   cd frontend && npm ci && npm run build && cd ..
   mkdir -p static && cp -r frontend/dist/* static/
   ```
3. Configure `config.yml`
4. Run:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```
