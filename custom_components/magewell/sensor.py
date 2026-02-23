"""Sensor platform for Magewell Pro Convert."""

import logging
import urllib.parse

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MagewellCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


def _get_ndi_source_name(summary: dict) -> str:
    """Extract friendly NDI source name from summary info."""
    ndi = summary.get("ndi", {})
    ndi_name = ndi.get("name", "unknown")
    ndi_url = ndi.get("url", "")

    if "name=" in ndi_url:
        try:
            raw = ndi_url.split("name=", 1)[1].split("&", 1)[0]
            friendly = urllib.parse.unquote(raw)
            if friendly:
                return friendly
        except (IndexError, ValueError):
            pass

    return ndi_name


def _get_resolution(summary: dict) -> str:
    """Build resolution string from summary."""
    ndi = summary.get("ndi", {})
    w = ndi.get("video-width", 0)
    h = ndi.get("video-height", 0)
    rate = ndi.get("video-field-rate", 0)
    if w and h:
        return f"{w}x{h}@{rate}fps"
    return ""


class MagewellEntity(CoordinatorEntity):
    """Base class for Magewell entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MagewellCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        """Return device info to group entities."""
        summary = self.coordinator.data.get("summary", {}) if self.coordinator.data else {}
        device = summary.get("device", {})
        ndi = summary.get("ndi", {})
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": device.get("name", "Magewell Pro Convert"),
            "manufacturer": "Magewell",
            "model": device.get("product", "Pro Convert"),
            "sw_version": device.get("firmware-version", ""),
            "serial_number": device.get("serial-number", ""),
            "configuration_url": f"http://{self._entry.data['host']}",
        }


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Magewell sensors from a config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([
        MagewellStatusSensor(coordinator, entry),
        MagewellNdiSourceSensor(coordinator, entry),
        MagewellCpuSensor(coordinator, entry),
        MagewellTemperatureSensor(coordinator, entry),
    ])


class MagewellStatusSensor(MagewellEntity, SensorEntity):
    """Sensor showing overall device status."""

    _attr_translation_key = "status"
    _attr_icon = "mdi:video-check"

    def __init__(self, coordinator: MagewellCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_name = "Status"

    @property
    def native_value(self) -> str | None:
        """Return ok or error."""
        if self.coordinator.data is None:
            return None
        summary = self.coordinator.data.get("summary", {})
        return "ok" if summary.get("status") == 0 else "error"

    @property
    def extra_state_attributes(self) -> dict:
        """Return device details."""
        if self.coordinator.data is None:
            return {}
        summary = self.coordinator.data.get("summary", {})
        device = summary.get("device", {})
        return {
            "device_name": device.get("name", ""),
            "firmware": device.get("firmware-version", ""),
            "uptime": device.get("up-time", 0),
        }


class MagewellNdiSourceSensor(MagewellEntity, SensorEntity):
    """Sensor showing the current NDI source name."""

    _attr_icon = "mdi:video-input-hdmi"

    def __init__(self, coordinator: MagewellCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ndi_source"
        self._attr_name = "NDI Source"

    @property
    def native_value(self) -> str | None:
        """Return the friendly NDI source name."""
        if self.coordinator.data is None:
            return None
        summary = self.coordinator.data.get("summary", {})
        return _get_ndi_source_name(summary)

    @property
    def extra_state_attributes(self) -> dict:
        """Return NDI connection details."""
        if self.coordinator.data is None:
            return {}
        summary = self.coordinator.data.get("summary", {})
        ndi = summary.get("ndi", {})
        return {
            "connected": ndi.get("connected", False),
            "video_resolution": _get_resolution(summary),
            "ip_addr": ndi.get("ip-addr", ""),
        }


class MagewellCpuSensor(MagewellEntity, SensorEntity):
    """Sensor showing CPU usage."""

    _attr_icon = "mdi:cpu-64-bit"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MagewellCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_cpu_usage"
        self._attr_name = "CPU Usage"

    @property
    def native_value(self) -> float | None:
        """Return CPU usage percentage."""
        if self.coordinator.data is None:
            return None
        summary = self.coordinator.data.get("summary", {})
        device = summary.get("device", {})
        return device.get("cpu-usage")


class MagewellTemperatureSensor(MagewellEntity, SensorEntity):
    """Sensor showing core temperature."""

    _attr_icon = "mdi:thermometer"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MagewellCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_core_temp"
        self._attr_name = "Core Temperature"

    @property
    def native_value(self) -> float | None:
        """Return core temperature in Celsius."""
        if self.coordinator.data is None:
            return None
        summary = self.coordinator.data.get("summary", {})
        device = summary.get("device", {})
        return device.get("core-temp")
