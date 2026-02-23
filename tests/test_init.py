"""Tests for the Magewell integration setup and teardown."""

from unittest.mock import AsyncMock

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.magewell.api import MagewellAuthError

from .conftest import setup_integration


async def test_setup_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test successful setup of a config entry."""
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    mock_magewell_client_init.login.assert_awaited_once()


async def test_setup_entry_auth_error(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test setup fails with auth error and triggers reauth."""
    mock_magewell_client_init.login.side_effect = MagewellAuthError("bad creds")

    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    mock_magewell_client_init.close.assert_awaited_once()


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test unloading a config entry."""
    await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    mock_magewell_client_init.close.assert_awaited_once()
