"""Magewell Pro Convert integration."""

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError

from .api import MagewellAuthError, MagewellClient
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import MagewellCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class MagewellRuntimeData:
    """Runtime data for the Magewell integration."""

    client: MagewellClient
    coordinator: MagewellCoordinator


type MagewellConfigEntry = ConfigEntry[MagewellRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: MagewellConfigEntry) -> bool:
    """Set up Magewell Pro Convert from a config entry."""
    client = MagewellClient(
        host=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )

    try:
        await client.login()
    except MagewellAuthError as err:
        await client.close()
        raise ConfigEntryAuthFailed from err

    coordinator = MagewellCoordinator(
        hass,
        client,
        scan_interval=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = MagewellRuntimeData(client=client, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MagewellConfigEntry) -> bool:
    """Unload a config entry."""
    # Raise rather than return False so the user sees why (HA 2026.11). Success
    # still returns True: HA releases before 2026.11 require a bool here.
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        raise ConfigEntryError(translation_domain=DOMAIN, translation_key="unload_failed")
    await entry.runtime_data.client.close()
    return True
