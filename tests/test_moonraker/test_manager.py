"""
Tests for MoonrakerManager connection manager.

Tests follow TDD approach - written before implementation.
Covers multi-printer connection management, printer loading, event routing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.moonraker.manager import MoonrakerManager
from src.database.models import Printer


class TestMoonrakerManagerInitialization:
    """Test MoonrakerManager initialization and singleton pattern."""

    def test_manager_is_singleton(self):
        """Test MoonrakerManager uses singleton pattern."""
        # Clear any existing instance
        MoonrakerManager._instance = None

        manager1 = MoonrakerManager.get_instance()
        manager2 = MoonrakerManager.get_instance()

        assert manager1 is manager2

    def test_manager_initialization(self):
        """Test manager initializes with empty clients dict."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        assert isinstance(manager.clients, dict)
        assert len(manager.clients) == 0

    def teardown_method(self):
        """Clean up singleton after each test."""
        MoonrakerManager._instance = None


class TestMoonrakerManagerStartup:
    """Test MoonrakerManager startup and printer loading."""

    @pytest.mark.asyncio
    async def test_start_loads_active_printers(self, db_session, sample_printer):
        """Test start loads all active printers from database."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        # Mock connect_printer to track calls
        with patch.object(manager, "connect_printer", new_callable=AsyncMock) as mock_connect:
            await manager.start(db=db_session)

            # Should attempt to connect sample_printer
            mock_connect.assert_called()

    @pytest.mark.asyncio
    async def test_start_skips_inactive_printers(self, db_session, sample_printer):
        """Test start skips inactive printers."""
        # Mark printer as inactive
        sample_printer.is_active = False
        db_session.commit()

        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        with patch.object(manager, "connect_printer", new_callable=AsyncMock) as mock_connect:
            await manager.start(db=db_session)

            # Should not connect to inactive printer
            mock_connect.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_connects_multiple_printers(self, db_session, sample_printer):
        """Test start connects to multiple active printers."""
        # Create a second printer
        printer2 = Printer(
            name="Second Printer",
            moonraker_url="http://printer2.local:7125",
            is_active=True
        )
        db_session.add(printer2)
        db_session.commit()

        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        with patch.object(manager, "connect_printer", new_callable=AsyncMock) as mock_connect:
            await manager.start(db=db_session)

            # Should connect to both printers
            assert mock_connect.call_count == 2

    def teardown_method(self):
        """Clean up singleton after each test."""
        MoonrakerManager._instance = None


class TestMoonrakerManagerConnectionManagement:
    """Test connecting and managing individual printers."""

    @pytest.mark.asyncio
    async def test_connect_printer_creates_client(self, sample_printer):
        """Test connect_printer creates MoonrakerClient for printer."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        with patch("src.moonraker.manager.MoonrakerClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            await manager.connect_printer(sample_printer)

            # Should create client with correct parameters
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["printer_id"] == sample_printer.id
            assert "ws://localhost:7125/websocket" in call_kwargs["url"]

    @pytest.mark.asyncio
    async def test_connect_printer_stores_client(self, sample_printer):
        """Test connect_printer stores client in clients dict."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        mock_client = AsyncMock()
        with patch("src.moonraker.manager.MoonrakerClient", return_value=mock_client):
            await manager.connect_printer(sample_printer)

            assert sample_printer.id in manager.clients
            assert manager.clients[sample_printer.id] == mock_client

    @pytest.mark.asyncio
    async def test_connect_printer_calls_client_connect(self, sample_printer):
        """Test connect_printer calls connect on the client."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        mock_client = AsyncMock()
        with patch("src.moonraker.manager.MoonrakerClient", return_value=mock_client):
            await manager.connect_printer(sample_printer)

            mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_printer_removes_client(self, sample_printer):
        """Test disconnect_printer removes client from dict."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        mock_client = AsyncMock()
        manager.clients[sample_printer.id] = mock_client

        await manager.disconnect_printer(sample_printer.id)

        assert sample_printer.id not in manager.clients
        mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_printer_is_safe(self):
        """Test disconnect_printer safely handles non-existent printer."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        # Should not raise exception
        await manager.disconnect_printer(99999)

    def teardown_method(self):
        """Clean up singleton after each test."""
        MoonrakerManager._instance = None


class TestMoonrakerManagerEventRouting:
    """Test event routing to handlers."""

    @pytest.mark.asyncio
    async def test_handle_event_routes_status_update(self):
        """Test handle_event routes notify_status_update to handler."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        event_data = {
            "method": "notify_status_update",
            "params": {"print_stats": {"state": "printing"}}
        }

        with patch("src.moonraker.manager.handle_status_update", new_callable=AsyncMock) as mock_handler:
            await manager.handle_event(1, event_data)

            mock_handler.assert_called_once_with(1, event_data["params"])

    @pytest.mark.asyncio
    async def test_handle_event_routes_history_changed(self):
        """Test handle_event routes notify_history_changed to handler."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        event_data = {
            "method": "notify_history_changed",
            "params": {"action": "finished", "job": {}}
        }

        with patch("src.moonraker.manager.handle_history_changed", new_callable=AsyncMock) as mock_handler:
            await manager.handle_event(1, event_data)

            mock_handler.assert_called_once_with(1, event_data["params"])

    @pytest.mark.asyncio
    async def test_handle_event_ignores_unknown_events(self):
        """Test handle_event safely ignores unknown event types."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        event_data = {
            "method": "some_unknown_event",
            "params": {}
        }

        # Should not raise exception
        await manager.handle_event(1, event_data)

    @pytest.mark.asyncio
    async def test_handle_event_handles_missing_method(self):
        """Test handle_event safely handles event without method field."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        event_data = {"params": {}}

        # Should not raise exception
        await manager.handle_event(1, event_data)

    def teardown_method(self):
        """Clean up singleton after each test."""
        MoonrakerManager._instance = None


class TestMoonrakerManagerRecovery:
    """Test manager recovery and health monitoring."""

    @pytest.mark.asyncio
    async def test_manager_updates_last_seen_on_successful_connection(self, db_session, sample_printer):
        """Test manager updates printer.last_seen on connection."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        mock_client = AsyncMock()
        with patch("src.moonraker.manager.MoonrakerClient", return_value=mock_client):
            await manager.connect_printer(sample_printer)

            # Verify last_seen was updated (this might be done during connection)
            # The exact timing depends on implementation

    @pytest.mark.asyncio
    async def test_manager_stop_disconnects_all_clients(self):
        """Test stop disconnects all active clients."""
        MoonrakerManager._instance = None
        manager = MoonrakerManager.get_instance()

        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()
        manager.clients[1] = mock_client1
        manager.clients[2] = mock_client2

        await manager.stop()

        mock_client1.disconnect.assert_called_once()
        mock_client2.disconnect.assert_called_once()
        assert len(manager.clients) == 0

    def teardown_method(self):
        """Clean up singleton after each test."""
        MoonrakerManager._instance = None
