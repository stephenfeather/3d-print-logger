# 3D Print Logger

![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/stephenfeather/3d-print-logger?utm_source=oss&utm_medium=github&utm_campaign=stephenfeather%2F3d-print-logger&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)

Self-hosted application for logging and analyzing 3D print jobs from multiple Klipper/Moonraker printers.

## Features

- **Multi-Printer Support**: Monitor and log jobs from multiple Klipper/Moonraker printers simultaneously
- **Real-Time Updates**: WebSocket connections to Moonraker for live job tracking
- **Job History**: Complete history of all print jobs with detailed metadata
- **Gcode Parsing**: Extract slicer settings from OrcaSlicer gcode files
- **Analytics Dashboard**: Statistics and insights across all printers
- **API Key Authentication**: Secure access to the REST API
- **Database Flexibility**: SQLite for simple setups, MySQL for production deployments

## Requirements

- Python 3.10+
- Klipper/Moonraker printer(s)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/stephenfeather/3d-print-logger.git
   cd 3d-print-logger
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy and configure settings:
   ```bash
   cp config.example.yml config.yml
   # Edit config.yml with your settings
   ```

5. Initialize the database:
   ```bash
   alembic upgrade head
   ```

6. Run the application:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

## Configuration

See `config.example.yml` for all available configuration options.

### Database

The application supports two database backends:

- **SQLite** (default): Simple file-based database, ideal for single-machine deployments
- **MySQL 8**: Production-grade database for larger deployments

### Adding Printers

Use the REST API to add printers:

```bash
curl -X POST http://localhost:8000/api/printers \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Printer 1",
    "location": "Office",
    "moonraker_url": "http://printer1.local:7125"
  }'
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

Install development dependencies:

```bash
pip install -r requirements.txt
# or
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

## Docker

Build and run with Docker:

```bash
cd docker
docker-compose up -d
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please read the contributing guidelines before submitting PRs.
