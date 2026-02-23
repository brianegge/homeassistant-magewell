"""Tests for the Magewell select platform."""

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.magewell.api import MagewellApiError

from .conftest import setup_integration


async def test_select_entity_options(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test select entity lists discovered NDI sources."""
    await setup_integration(hass, mock_config_entry)

    state = hass.states.get("select.magewelltest_ndi_source_select")
    assert state is not None
    assert state.attributes["options"] == ["Camera 1", "Camera 2", "Camera 3"]
    assert state.state == "Camera 1"


async def test_select_option(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test selecting an NDI source calls set_channel."""
    await setup_integration(hass, mock_config_entry)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.magewelltest_ndi_source_select", "option": "Camera 2"},
        blocking=True,
    )

    mock_magewell_client_init.set_channel.assert_awaited_once_with("Camera 2")


async def test_select_option_api_error(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test select handles API error gracefully."""
    await setup_integration(hass, mock_config_entry)

    mock_magewell_client_init.set_channel.side_effect = MagewellApiError("fail")

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.magewelltest_ndi_source_select", "option": "Camera 2"},
        blocking=True,
    )

    # Should not raise, error is logged
    mock_magewell_client_init.set_channel.assert_awaited_once_with("Camera 2")
