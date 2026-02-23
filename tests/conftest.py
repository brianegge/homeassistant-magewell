"""Fixtures for Magewell tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from custom_components.magewell.const import CONF_SCAN_INTERVAL, DOMAIN

from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield

MOCK_HOST = "192.168.1.100"
MOCK_USER_INPUT = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: "Admin",
    CONF_PASSWORD: "secret",
    CONF_SCAN_INTERVAL: 30,
}

MOCK_SUMMARY_INFO = {
    "status": 0,
    "device": {
        "name": "MagewellTest",
        "product": "Pro Convert",
        "firmware-version": "1.3.456",
        "serial-number": "ABC123",
        "cpu-usage": 25.0,
        "core-temp": 45.0,
        "up-time": 86400,
    },
    "ndi": {
        "name": "MAGEWELL (Test)",
        "url": "ndi://192.168.1.50:5961?name=Camera%201",
        "connected": True,
        "video-width": 1920,
        "video-height": 1080,
        "video-field-rate": 60,
        "ip-addr": "192.168.1.50",
    },
}

MOCK_CHANNEL = {
    "status": 0,
    "ndi-name": "Camera 1",
}

MOCK_NDI_SOURCES = ["Camera 1", "Camera 2", "Camera 3"]


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Prevent actual async_setup_entry from running."""
    with patch(
        "custom_components.magewell.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a MockConfigEntry for Magewell."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_HOST,
        data=MOCK_USER_INPUT,
        title=f"Magewell ({MOCK_HOST})",
    )


@pytest.fixture
def mock_magewell_client() -> Generator[AsyncMock]:
    """Mock the MagewellClient for config flow tests."""
    with patch(
        "custom_components.magewell.config_flow.MagewellClient",
        autospec=True,
    ) as mock_client_class:
        client = mock_client_class.return_value
        client.login = AsyncMock(return_value=None)
        client.get_summary_info = AsyncMock(return_value=MOCK_SUMMARY_INFO)
        client.get_channel = AsyncMock(return_value=MOCK_CHANNEL)
        client.get_ndi_sources = AsyncMock(return_value=MOCK_NDI_SOURCES)
        client.close = AsyncMock(return_value=None)
        client.set_channel = AsyncMock(return_value={"status": 0})
        yield client


@pytest.fixture
def mock_magewell_client_init() -> Generator[AsyncMock]:
    """Mock MagewellClient in __init__.py for integration setup tests."""
    with patch(
        "custom_components.magewell.MagewellClient",
        autospec=True,
    ) as mock_client_class:
        client = mock_client_class.return_value
        client.login = AsyncMock(return_value=None)
        client.get_summary_info = AsyncMock(return_value=MOCK_SUMMARY_INFO)
        client.get_channel = AsyncMock(return_value=MOCK_CHANNEL)
        client.get_ndi_sources = AsyncMock(return_value=MOCK_NDI_SOURCES)
        client.close = AsyncMock(return_value=None)
        client.set_channel = AsyncMock(return_value={"status": 0})
        yield client


async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Set up the Magewell integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
