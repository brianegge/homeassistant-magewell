"""Binary sensor platform for Magewell Pro Convert."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MagewellCoordinator
from .sensor import MagewellEntity, _get_ndi_source_name, _get_resolution


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Magewell binary sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([MagewellNdiConnectedSensor(coordinator, entry)])


class MagewellNdiConnectedSensor(MagewellEntity, BinarySensorEntity):
    """Binary sensor indicating NDI connection status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:video-input-hdmi"

    def __init__(self, coordinator: MagewellCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ndi_connected"
        self._attr_name = "NDI Connected"

    @property
    def is_on(self) -> bool | None:
        """Return true if NDI source is connected."""
        if self.coordinator.data is None:
            return None
        summary = self.coordinator.data.get("summary", {})
        ndi = summary.get("ndi", {})
        return ndi.get("connected", False)

    @property
    def extra_state_attributes(self) -> dict:
        """Return NDI source details."""
        if self.coordinator.data is None:
            return {}
        summary = self.coordinator.data.get("summary", {})
        return {
            "ndi_source": _get_ndi_source_name(summary),
            "video_resolution": _get_resolution(summary),
        }
