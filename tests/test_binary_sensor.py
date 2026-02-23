"""Tests for the Magewell binary sensor platform."""

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from .conftest import setup_integration


async def test_ndi_connected_sensor(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test NDI connected binary sensor shows on when connected."""
    await setup_integration(hass, mock_config_entry)

    state = hass.states.get("binary_sensor.magewelltest_ndi_connected")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["ndi_source"] == "Camera 1"
    assert state.attributes["video_resolution"] == "1920x1080@60fps"


async def test_ndi_disconnected_sensor(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test NDI connected binary sensor shows off when disconnected."""
    mock_magewell_client_init.get_summary_info.return_value = {
        "status": 0,
        "device": {
            "name": "MagewellTest",
            "product": "Pro Convert",
            "firmware-version": "1.3.456",
            "serial-number": "ABC123",
            "cpu-usage": 10.0,
            "core-temp": 40.0,
            "up-time": 100,
        },
        "ndi": {
            "name": "",
            "url": "",
            "connected": False,
            "ip-addr": "",
        },
    }

    await setup_integration(hass, mock_config_entry)

    state = hass.states.get("binary_sensor.magewelltest_ndi_connected")
    assert state is not None
    assert state.state == "off"
