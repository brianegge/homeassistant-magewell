"""Diagnostics support for Magewell Pro Convert."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import MagewellConfigEntry

TO_REDACT = {CONF_PASSWORD, CONF_USERNAME}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MagewellConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator

    return {
        "config_entry": async_redact_data(dict(entry.data), TO_REDACT),
        "coordinator_data": {
            "summary": coordinator.data.get("summary", {}) if coordinator.data else {},
            "channel": coordinator.data.get("channel", {}) if coordinator.data else {},
            "ndi_sources": coordinator.data.get("ndi_sources", []) if coordinator.data else [],
        },
    }
