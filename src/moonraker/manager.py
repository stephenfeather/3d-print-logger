"""
Multi-printer connection manager for 3D Print Logger.

Manages WebSocket connections to multiple Moonraker instances,
handles reconnection logic, and routes events to handlers.
"""

import logging
from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.database.crud import get_active_printers, update_printer_last_seen
from src.database.models import Printer
from src.moonraker.client import MoonrakerClient
from src.moonraker.handlers import handle_history_changed, handle_status_update

logger = logging.getLogger(__name__)


class MoonrakerManager:
    """
    Singleton manager for Moonraker WebSocket connections.

    Manages per-printer WebSocket clients, handles event routing,
    and maintains connection health across multiple printer instances.
    """

    _instance: Optional["MoonrakerManager"] = None

    def __init__(self):
        """Initialize manager with empty client dict."""
        self.clients: Dict[int, MoonrakerClient] = {}

    @classmethod
    def get_instance(cls) -> "MoonrakerManager":
        """
        Get or create singleton instance.

        Returns:
            MoonrakerManager: Singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self, db: Session) -> None:
        """
        Start manager and connect all active printers.

        Loads active printers from database and initiates
        WebSocket connections for each.

        Args:
            db: Database session
        """
        logger.info("Starting Moonraker manager")

        try:
            printers = get_active_printers(db)
            logger.info(f"Found {len(printers)} active printers")

            for printer in printers:
                try:
                    await self.connect_printer(printer)
                except Exception as e:
                    logger.error(f"Failed to connect printer {printer.id}: {e}")

            logger.info("Moonraker manager started")

        except Exception as e:
            logger.error(f"Failed to start Moonraker manager: {e}")
            raise

    async def connect_printer(self, printer: Printer) -> None:
        """
        Connect to a printer and store client.

        Creates a MoonrakerClient for the printer and initiates
        WebSocket connection.

        Args:
            printer: Printer model instance

        Raises:
            ConnectionError: If connection fails
        """
        logger.info(f"Connecting to printer {printer.id}: {printer.name}")

        # Create client
        client = MoonrakerClient(
            printer_id=printer.id,
            url=printer.moonraker_url,
            api_key=printer.moonraker_api_key,
            event_handler=self.handle_event,
        )

        # Connect
        await client.connect()

        # Store client
        self.clients[printer.id] = client

        logger.info(f"Printer {printer.id} connected")

    async def disconnect_printer(self, printer_id: int) -> None:
        """
        Disconnect a printer and remove client.

        Args:
            printer_id: ID of printer to disconnect
        """
        if printer_id not in self.clients:
            logger.warning(f"Printer {printer_id} not found in clients")
            return

        client = self.clients[printer_id]
        logger.info(f"Disconnecting printer {printer_id}")

        try:
            await client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting printer {printer_id}: {e}")

        del self.clients[printer_id]
        logger.info(f"Printer {printer_id} disconnected")

    async def handle_event(self, printer_id: int, event: dict) -> None:
        """
        Route event to appropriate handler.

        Dispatches events to specific handlers based on event type.

        Args:
            printer_id: ID of printer sending event
            event: Event data dictionary
        """
        method = event.get("method")
        params = event.get("params", {})

        if method == "notify_status_update":
            await handle_status_update(printer_id, params)

        elif method == "notify_history_changed":
            await handle_history_changed(printer_id, params)

        else:
            logger.debug(
                f"Received unknown event from printer {printer_id}: {method}"
            )

    async def stop(self) -> None:
        """
        Stop manager and disconnect all printers.

        Gracefully disconnects all active clients.
        """
        logger.info("Stopping Moonraker manager")

        # Disconnect all clients
        printer_ids = list(self.clients.keys())
        for printer_id in printer_ids:
            try:
                await self.disconnect_printer(printer_id)
            except Exception as e:
                logger.error(f"Error disconnecting printer {printer_id}: {e}")

        logger.info("Moonraker manager stopped")
