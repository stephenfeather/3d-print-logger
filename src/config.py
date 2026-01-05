"""
Configuration management for 3D Print Logger.

Handles loading configuration from YAML files, environment variables,
and provides typed configuration objects for the application.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
import yaml


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    type: str = "sqlite"
    path: str = "./data/printlog.db"
    host: str = "localhost"
    port: int = 3306
    user: str = "printlog"
    password: str = ""
    database: str = "printlog"


@dataclass
class MoonrakerConfig:
    """Moonraker connection configuration."""

    reconnect_delay: int = 5
    max_reconnect_delay: int = 60
    health_check_interval: int = 30


@dataclass
class ApiConfig:
    """API server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000"])


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    file: str = "./logs/printlog.log"


@dataclass
class AppConfig:
    """Main application configuration."""

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    moonraker: MoonrakerConfig = field(default_factory=MoonrakerConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def _deep_update(base_dict: dict, update_dict: dict) -> dict:
    """Recursively update a dictionary with another dictionary."""
    for key, value in update_dict.items():
        if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
            _deep_update(base_dict[key], value)
        else:
            base_dict[key] = value
    return base_dict


def load_config_from_file(config_path: str) -> dict:
    """Load configuration from a YAML file."""
    path = Path(config_path)
    if not path.exists():
        return {}

    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}


def load_config_from_env() -> dict:
    """Load configuration from environment variables."""
    config: dict = {}

    # Database configuration from environment
    if os.getenv("DATABASE_TYPE"):
        if "database" not in config:
            config["database"] = {}
        config["database"]["type"] = os.getenv("DATABASE_TYPE")

    if os.getenv("DATABASE_PATH"):
        if "database" not in config:
            config["database"] = {}
        config["database"]["path"] = os.getenv("DATABASE_PATH")

    if os.getenv("DATABASE_HOST"):
        if "database" not in config:
            config["database"] = {}
        config["database"]["host"] = os.getenv("DATABASE_HOST")

    if os.getenv("DATABASE_PORT"):
        if "database" not in config:
            config["database"] = {}
        config["database"]["port"] = int(os.getenv("DATABASE_PORT", "3306"))

    if os.getenv("DATABASE_USER"):
        if "database" not in config:
            config["database"] = {}
        config["database"]["user"] = os.getenv("DATABASE_USER")

    if os.getenv("DATABASE_PASSWORD"):
        if "database" not in config:
            config["database"] = {}
        config["database"]["password"] = os.getenv("DATABASE_PASSWORD")

    if os.getenv("DATABASE_NAME"):
        if "database" not in config:
            config["database"] = {}
        config["database"]["database"] = os.getenv("DATABASE_NAME")

    # Logging level
    if os.getenv("LOG_LEVEL"):
        if "logging" not in config:
            config["logging"] = {}
        config["logging"]["level"] = os.getenv("LOG_LEVEL")

    return config


def build_config(config_dict: dict) -> AppConfig:
    """Build AppConfig from a dictionary."""
    database_config = DatabaseConfig(**config_dict.get("database", {}))
    moonraker_config = MoonrakerConfig(**config_dict.get("moonraker", {}))
    api_config = ApiConfig(**config_dict.get("api", {}))
    logging_config = LoggingConfig(**config_dict.get("logging", {}))

    return AppConfig(
        database=database_config,
        moonraker=moonraker_config,
        api=api_config,
        logging=logging_config
    )


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the application configuration.

    Loads configuration from:
    1. Default values
    2. Configuration file (if exists)
    3. Environment variables (override file values)

    Returns:
        AppConfig: The application configuration.
    """
    global _config

    if _config is not None:
        return _config

    # Start with empty config (defaults come from dataclass)
    config_dict: dict = {}

    # Load from config file
    config_path = os.getenv("CONFIG_PATH", "config.yml")
    file_config = load_config_from_file(config_path)
    _deep_update(config_dict, file_config)

    # Override with environment variables
    env_config = load_config_from_env()
    _deep_update(config_dict, env_config)

    _config = build_config(config_dict)
    return _config


def reset_config() -> None:
    """Reset the global configuration. Useful for testing."""
    global _config
    _config = None


def set_config(config: AppConfig) -> None:
    """Set the global configuration. Useful for testing."""
    global _config
    _config = config
