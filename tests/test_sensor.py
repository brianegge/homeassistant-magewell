"""Tests for the Magewell sensor platform."""

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.magewell.sensor import _get_ndi_source_name, _get_resolution

from .conftest import MOCK_SUMMARY_INFO, setup_integration


async def test_sensors_created(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test that all four sensors are created."""
    await setup_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.magewelltest_status")
    assert state is not None
    assert state.state == "ok"
    assert state.attributes["device_name"] == "MagewellTest"
    assert state.attributes["firmware"] == "1.3.456"
    assert state.attributes["uptime"] == 86400

    state = hass.states.get("sensor.magewelltest_ndi_source")
    assert state is not None
    assert state.state == "Camera 1"
    assert state.attributes["connected"] is True
    assert state.attributes["video_resolution"] == "1920x1080@60fps"
    assert state.attributes["ip_addr"] == "192.168.1.50"


async def test_disabled_by_default_sensors(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test that CPU usage and core temperature sensors are disabled by default."""
    await setup_integration(hass, mock_config_entry)

    ent_reg = er.async_get(hass)

    cpu_entry = ent_reg.async_get("sensor.magewelltest_cpu_usage")
    assert cpu_entry is not None
    assert cpu_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    temp_entry = ent_reg.async_get("sensor.magewelltest_core_temperature")
    assert temp_entry is not None
    assert temp_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    # Disabled entities should not have state
    assert hass.states.get("sensor.magewelltest_cpu_usage") is None
    assert hass.states.get("sensor.magewelltest_core_temperature") is None


def test_get_ndi_source_name_from_url() -> None:
    """Test NDI source name extraction from URL."""
    summary = {
        "ndi": {
            "name": "MAGEWELL (Fallback)",
            "url": "ndi://10.0.0.1:5961?name=My%20Camera",
        }
    }
    assert _get_ndi_source_name(summary) == "My Camera"


def test_get_ndi_source_name_fallback_to_name() -> None:
    """Test NDI source name falls back to ndi.name when no URL param."""
    summary = {
        "ndi": {
            "name": "MAGEWELL (Test)",
            "url": "ndi://10.0.0.1:5961",
        }
    }
    assert _get_ndi_source_name(summary) == "MAGEWELL (Test)"


def test_get_ndi_source_name_empty_summary() -> None:
    """Test NDI source name with empty summary."""
    assert _get_ndi_source_name({}) == "unknown"


def test_get_resolution() -> None:
    """Test resolution string building."""
    summary = {
        "ndi": {
            "video-width": 1920,
            "video-height": 1080,
            "video-field-rate": 60,
        }
    }
    assert _get_resolution(summary) == "1920x1080@60fps"


def test_get_resolution_no_video() -> None:
    """Test resolution returns empty string when no video info."""
    assert _get_resolution({}) == ""
    assert _get_resolution({"ndi": {}}) == ""
