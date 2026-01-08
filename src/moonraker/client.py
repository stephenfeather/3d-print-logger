"""
WebSocket client for Moonraker communication.

Provides a per-printer WebSocket client for connecting to
Moonraker instances and receiving real-time updates.
"""

import asyncio
import json
import logging
import random
from typing import Callable, Optional

import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class MoonrakerClient:
    """
    WebSocket client for single Moonraker printer instance.

    Manages connection, subscription to events, message listening,
    and reconnection with exponential backoff.
    """

    def __init__(
        self,
        printer_id: int,
        url: str,
        api_key: Optional[str],
        event_handler: Callable
    ):
        """
        Initialize Moonraker client.

        Args:
            printer_id: Unique identifier for the printer
            url: HTTP URL of Moonraker instance (e.g., http://localhost:7125)
            api_key: Optional API key for Moonraker authentication
            event_handler: Async callback function for handling events
        """
        self.printer_id = printer_id
        self.ws_url = self._convert_to_ws_url(url)
        self.api_key = api_key
        self.event_handler = event_handler
        self.ws: Optional[WebSocketClientProtocol] = None
        self.running = False

    @staticmethod
    def _convert_to_ws_url(http_url: str) -> str:
        """
        Convert HTTP URL to WebSocket URL.

        Args:
            http_url: HTTP URL (e.g., http://localhost:7125)

        Returns:
            WebSocket URL (e.g., ws://localhost:7125/websocket)
        """
        # Replace http with ws, https with wss
        ws_url = http_url.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        # Append /websocket path if not present
        if not ws_url.endswith("/websocket"):
            ws_url = ws_url.rstrip("/") + "/websocket"
        return ws_url

    async def _establish_connection(self) -> None:
        """
        Establish WebSocket connection and subscribe to events.

        Internal method that creates the WebSocket and subscribes to events
        without spawning a new listen task. Used for both initial connection
        and reconnection.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Close old connection if exists
            if self.ws:
                try:
                    await self.ws.close()
                except Exception:
                    pass  # Ignore errors closing old connection

            logger.info(f"Connecting to Moonraker at {self.ws_url}")
            self.ws = await websockets.connect(self.ws_url)
            logger.info(f"Connected to printer {self.printer_id}")

            # Subscribe to print_stats for status updates
            await self.subscribe("print_stats")

            # Subscribe to virtual_sdcard for print progress
            await self.subscribe("virtual_sdcard")

            # Query current state immediately after subscribing
            # This ensures we get the initial print_stats even if not changing
            await self.query_printer_objects()

            # Note: History notifications (notify_history_changed) are sent
            # automatically by Moonraker, no subscription needed

        except Exception as e:
            logger.error(f"Failed to connect to printer {self.printer_id}: {e}")
            raise ConnectionError(f"Failed to connect to {self.ws_url}") from e

    async def connect(self) -> None:
        """
        Connect to Moonraker and start listen loop.

        Public method for initial connection. Establishes WebSocket
        connection and spawns the listen task.

        Raises:
            ConnectionError: If connection fails
        """
        await self._establish_connection()

        # Start listen loop (only on initial connect, not reconnect)
        self.running = True
        asyncio.create_task(self.listen())

    async def disconnect(self) -> None:
        """
        Disconnect WebSocket and stop listen loop.
        """
        self.running = False
        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                logger.error(
                    f"Error closing WebSocket for printer {self.printer_id}: {e}"
                )

    async def subscribe(self, object_name: str) -> None:
        """
        Subscribe to Moonraker object updates.

        Sends JSON-RPC request to subscribe to changes in a specific object.

        Args:
            object_name: Object to subscribe to (e.g., "print_stats")
        """
        if not self.ws:
            raise RuntimeError(
                f"WebSocket not connected for printer {self.printer_id}"
            )

        request = {
            "jsonrpc": "2.0",
            "method": "printer.objects.subscribe",
            "params": {"objects": {object_name: None}},
            "id": random.randint(1, 10000),
        }

        try:
            await self.ws.send(json.dumps(request))
            logger.debug(
                f"Subscribed printer {self.printer_id} to {object_name}"
            )
        except Exception as e:
            logger.error(
                f"Failed to subscribe printer {self.printer_id} "
                f"to {object_name}: {e}"
            )

    async def query_printer_objects(self) -> None:
        """
        Query current printer object states.

        Requests current values for subscribed objects (print_stats, virtual_sdcard).
        The response will trigger a status update event with all current values.
        """
        if not self.ws:
            raise RuntimeError(
                f"WebSocket not connected for printer {self.printer_id}"
            )

        request = {
            "jsonrpc": "2.0",
            "method": "printer.objects.query",
            "params": {"objects": {"print_stats": None, "virtual_sdcard": None}},
            "id": random.randint(1, 10000),
        }

        try:
            await self.ws.send(json.dumps(request))
            logger.info(f"Queried printer {self.printer_id} objects")
        except Exception as e:
            logger.error(
                f"Failed to query printer {self.printer_id} objects: {e}"
            )

    async def listen(self) -> None:
        """
        Listen for WebSocket messages and route to event handler.

        Continuously receives messages from Moonraker and calls
        event_handler for processing. On error, triggers reconnection.
        """
        while self.running:
            try:
                if not self.ws:
                    logger.warning(
                        f"WebSocket disconnected for printer {self.printer_id}"
                    )
                    await self.reconnect()
                    continue

                message = await self.ws.recv()

                if not message:
                    logger.debug(
                        f"Empty message received from printer {self.printer_id}"
                    )
                    continue

                try:
                    data = json.loads(message)
                    await self.event_handler(self.printer_id, data)
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Failed to decode JSON from printer "
                        f"{self.printer_id}: {e}"
                    )

            except ConnectionError as e:
                logger.error(
                    f"Connection error for printer {self.printer_id}: {e}"
                )
                await self.reconnect()
            except asyncio.CancelledError:
                logger.info(f"Listen loop cancelled for printer {self.printer_id}")
                break
            except Exception as e:
                logger.error(
                    f"Unexpected error in listen loop for printer "
                    f"{self.printer_id}: {e}"
                )
                await self.reconnect()

    async def reconnect(self, max_attempts: int = 10) -> bool:
        """
        Reconnect to Moonraker with exponential backoff.

        Re-establishes the WebSocket connection without spawning a new
        listen task. The existing listen loop will continue using the
        new connection.

        Attempts to reconnect with delays: 5s, 10s, 30s, 60s (max).

        Args:
            max_attempts: Maximum number of reconnection attempts

        Returns:
            True if reconnection successful, False otherwise
        """
        base_delay = 5
        max_delay = 60

        for attempt in range(max_attempts):
            if not self.running:
                logger.info(f"Reconnect cancelled for printer {self.printer_id}")
                return False

            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.info(
                f"Reconnecting printer {self.printer_id} "
                f"(attempt {attempt + 1}/{max_attempts}) in {delay}s"
            )

            try:
                await asyncio.sleep(delay)
                # Use _establish_connection() instead of connect()
                # to avoid spawning a new listen task
                await self._establish_connection()
                logger.info(f"Successfully reconnected printer {self.printer_id}")
                return True
            except Exception as e:
                logger.debug(
                    f"Reconnection attempt {attempt + 1} failed "
                    f"for printer {self.printer_id}: {e}"
                )

        logger.error(
            f"Failed to reconnect printer {self.printer_id} "
            f"after {max_attempts} attempts"
        )
        return False
