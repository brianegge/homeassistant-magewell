"""Tests for the Magewell diagnostics platform."""

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.magewell.diagnostics import async_get_config_entry_diagnostics

from .conftest import MOCK_NDI_SOURCES, MOCK_SUMMARY_INFO, setup_integration


async def test_diagnostics(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test diagnostics output contains expected data with redacted credentials."""
    await setup_integration(hass, mock_config_entry)

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    # Credentials should be redacted
    assert diag["config_entry"]["username"] == "**REDACTED**"
    assert diag["config_entry"]["password"] == "**REDACTED**"

    # Host and scan_interval should be present
    assert diag["config_entry"]["host"] == "192.168.1.100"
    assert diag["config_entry"]["scan_interval"] == 30

    # Coordinator data should be present
    assert diag["coordinator_data"]["summary"] == MOCK_SUMMARY_INFO
    assert diag["coordinator_data"]["ndi_sources"] == MOCK_NDI_SOURCES
