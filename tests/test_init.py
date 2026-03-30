"""Tests for the Magewell integration setup and teardown."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from custom_components.magewell.api import MagewellApiError, MagewellAuthError
from custom_components.magewell.const import DOMAIN
from custom_components.magewell.coordinator import CONSECUTIVE_FAILURE_THRESHOLD

from .conftest import MOCK_CHANNEL, MOCK_NDI_SOURCES, MOCK_SUMMARY_INFO, setup_integration


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


async def test_coordinator_persistent_failure_creates_repair_issue(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test that consecutive failures create a repair issue."""
    await setup_integration(hass, mock_config_entry)

    coordinator = mock_config_entry.runtime_data.coordinator

    # Simulate consecutive failures up to threshold
    mock_magewell_client_init.get_summary_info.side_effect = MagewellApiError("offline")

    for _ in range(CONSECUTIVE_FAILURE_THRESHOLD):
        await coordinator.async_refresh()

    issue_reg = ir.async_get(hass)
    issue = issue_reg.async_get_issue(
        DOMAIN, f"persistent_connection_failure_{mock_config_entry.entry_id}"
    )
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.ERROR


async def test_coordinator_recovery_deletes_repair_issue(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test that recovery after persistent failure deletes the repair issue."""
    await setup_integration(hass, mock_config_entry)

    coordinator = mock_config_entry.runtime_data.coordinator

    # Create the persistent failure issue
    mock_magewell_client_init.get_summary_info.side_effect = MagewellApiError("offline")
    for _ in range(CONSECUTIVE_FAILURE_THRESHOLD):
        await coordinator.async_refresh()

    issue_reg = ir.async_get(hass)
    assert issue_reg.async_get_issue(
        DOMAIN, f"persistent_connection_failure_{mock_config_entry.entry_id}"
    ) is not None

    # Recover
    mock_magewell_client_init.get_summary_info.side_effect = None
    mock_magewell_client_init.get_summary_info.return_value = MOCK_SUMMARY_INFO
    await coordinator.async_refresh()

    assert issue_reg.async_get_issue(
        DOMAIN, f"persistent_connection_failure_{mock_config_entry.entry_id}"
    ) is None
