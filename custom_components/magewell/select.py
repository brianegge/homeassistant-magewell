"""Select platform for Magewell Pro Convert — NDI source picker."""

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import MagewellApiError
from .const import DOMAIN
from .coordinator import MagewellCoordinator
from .sensor import MagewellEntity, _get_ndi_source_name

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Magewell select entity from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    async_add_entities([MagewellNdiSourceSelect(coordinator, entry, client)])


class MagewellNdiSourceSelect(MagewellEntity, SelectEntity):
    """Select entity to choose the active NDI source."""

    _attr_icon = "mdi:video-switch"

    def __init__(self, coordinator: MagewellCoordinator, entry: ConfigEntry, client) -> None:
        """Initialize."""
        super().__init__(coordinator, entry)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_ndi_source_select"
        self._attr_name = "NDI Source Select"

    @property
    def options(self) -> list[str]:
        """Return discovered NDI sources as dropdown options."""
        if self.coordinator.data is None:
            return []
        return self.coordinator.data.get("ndi_sources", [])

    @property
    def current_option(self) -> str | None:
        """Return the currently active NDI source."""
        if self.coordinator.data is None:
            return None
        summary = self.coordinator.data.get("summary", {})
        current = _get_ndi_source_name(summary)
        # Return current only if it's in the options list
        if current in self.options:
            return current
        return current if self.options == [] else None

    async def async_select_option(self, option: str) -> None:
        """Switch the decoder to the selected NDI source."""
        try:
            await self._client.set_channel(option)
        except MagewellApiError as err:
            _LOGGER.error("Failed to set NDI source to %s: %s", option, err)
            return
        await self.coordinator.async_request_refresh()
