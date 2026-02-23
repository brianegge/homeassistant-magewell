"""Tests for the Magewell config flow."""

from unittest.mock import AsyncMock

import pytest

from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.magewell.api import MagewellApiError, MagewellAuthError
from custom_components.magewell.const import CONF_SCAN_INTERVAL, DOMAIN


async def test_full_user_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_magewell_client: AsyncMock,
) -> None:
    """Test a successful config flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "Admin",
            CONF_PASSWORD: "secret",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Magewell (192.168.1.100)"
    assert result["data"] == {
        CONF_HOST: "192.168.1.100",
        CONF_USERNAME: "Admin",
        CONF_PASSWORD: "secret",
        CONF_SCAN_INTERVAL: 30,
    }

    mock_magewell_client.login.assert_awaited_once()
    mock_magewell_client.get_summary_info.assert_awaited_once()
    mock_magewell_client.close.assert_awaited_once()


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (MagewellAuthError("bad creds"), "invalid_auth"),
        (MagewellApiError("timeout"), "cannot_connect"),
        (Exception("unexpected"), "cannot_connect"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_magewell_client: AsyncMock,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test error handling during config flow."""
    mock_magewell_client.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "Admin",
            CONF_PASSWORD: "wrong",
            CONF_SCAN_INTERVAL: 30,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": expected_error}
    mock_magewell_client.close.assert_awaited_once()


async def test_user_flow_recovery_after_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_magewell_client: AsyncMock,
) -> None:
    """Test recovery after initial error."""
    mock_magewell_client.login.side_effect = MagewellAuthError("bad")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "Admin",
            CONF_PASSWORD: "wrong",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    mock_magewell_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "Admin",
            CONF_PASSWORD: "correct",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_already_configured(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_magewell_client: AsyncMock,
    mock_config_entry,
) -> None:
    """Test abort when device is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "Admin",
            CONF_PASSWORD: "secret",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_flow_summary_info_fails(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_magewell_client: AsyncMock,
) -> None:
    """Test error when login succeeds but get_summary_info fails."""
    mock_magewell_client.get_summary_info.side_effect = Exception("device error")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "Admin",
            CONF_PASSWORD: "secret",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    mock_magewell_client.close.assert_awaited_once()


async def test_reauth_flow_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_magewell_client: AsyncMock,
    mock_config_entry,
) -> None:
    """Test successful reauthentication flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "Admin",
            CONF_PASSWORD: "new_password",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_PASSWORD] == "new_password"


async def test_reauth_flow_invalid_auth(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_magewell_client: AsyncMock,
    mock_config_entry,
) -> None:
    """Test reauth flow with invalid credentials."""
    mock_config_entry.add_to_hass(hass)
    mock_magewell_client.login.side_effect = MagewellAuthError("bad")

    result = await mock_config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "Admin",
            CONF_PASSWORD: "wrong",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_reconfigure_flow_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_magewell_client: AsyncMock,
    mock_config_entry,
) -> None:
    """Test successful reconfiguration flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.200",
            CONF_USERNAME: "Admin",
            CONF_PASSWORD: "new_secret",
            CONF_SCAN_INTERVAL: 60,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.200"
    assert mock_config_entry.data[CONF_PASSWORD] == "new_secret"
    assert mock_config_entry.data[CONF_SCAN_INTERVAL] == 60


async def test_reconfigure_flow_auth_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_magewell_client: AsyncMock,
    mock_config_entry,
) -> None:
    """Test reconfigure flow with invalid credentials."""
    mock_config_entry.add_to_hass(hass)
    mock_magewell_client.login.side_effect = MagewellAuthError("bad")

    result = await mock_config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.200",
            CONF_USERNAME: "Admin",
            CONF_PASSWORD: "wrong",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": "invalid_auth"}
