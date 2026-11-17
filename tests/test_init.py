"""Tests for the Magewell integration setup and teardown."""

import inspect
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from custom_components.magewell import coordinator as coordinator_module
from custom_components.magewell.api import MagewellApiError, MagewellAuthError
from custom_components.magewell.const import DOMAIN
from custom_components.magewell.coordinator import CONSECUTIVE_FAILURE_THRESHOLD

from .conftest import MOCK_SUMMARY_INFO, setup_integration


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


async def test_unload_entry_platform_failure(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
) -> None:
    """Test a failed platform unload raises instead of returning False."""
    await setup_integration(hass, mock_config_entry)

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        AsyncMock(return_value=False),
    ):
        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.FAILED_UNLOAD
    mock_magewell_client_init.close.assert_not_awaited()


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
    issue = issue_reg.async_get_issue(DOMAIN, f"persistent_connection_failure_{mock_config_entry.entry_id}")
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
    assert issue_reg.async_get_issue(DOMAIN, f"persistent_connection_failure_{mock_config_entry.entry_id}") is not None

    # Recover
    mock_magewell_client_init.get_summary_info.side_effect = None
    mock_magewell_client_init.get_summary_info.return_value = MOCK_SUMMARY_INFO
    await coordinator.async_refresh()

    assert issue_reg.async_get_issue(DOMAIN, f"persistent_connection_failure_{mock_config_entry.entry_id}") is None


@pytest.mark.parametrize("supported", [True, False])
async def test_repair_issue_config_entry_id(
    hass: HomeAssistant,
    mock_config_entry,
    mock_magewell_client_init: AsyncMock,
    supported: bool,
) -> None:
    """Test the repair issue is tied to the config entry only where HA supports it."""
    await setup_integration(hass, mock_config_entry)

    coordinator = mock_config_entry.runtime_data.coordinator
    mock_magewell_client_init.get_summary_info.side_effect = MagewellApiError("offline")

    with (
        patch("custom_components.magewell.coordinator.ISSUE_SUPPORTS_CONFIG_ENTRY", supported),
        patch("custom_components.magewell.coordinator.ir.async_create_issue") as mock_create_issue,
    ):
        for _ in range(CONSECUTIVE_FAILURE_THRESHOLD):
            await coordinator.async_refresh()

    mock_create_issue.assert_called_once()
    args, kwargs = mock_create_issue.call_args
    assert args[1:] == (DOMAIN, f"persistent_connection_failure_{mock_config_entry.entry_id}")
    if supported:
        assert kwargs["config_entry_id"] == mock_config_entry.entry_id
    else:
        assert "config_entry_id" not in kwargs


def test_issue_config_entry_support_detection() -> None:
    """Test the feature flag matches the installed HA's async_create_issue."""
    params = inspect.signature(ir.async_create_issue).parameters
    assert coordinator_module.ISSUE_SUPPORTS_CONFIG_ENTRY is ("config_entry_id" in params)
