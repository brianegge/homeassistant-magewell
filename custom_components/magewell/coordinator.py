"""DataUpdateCoordinator for Magewell Pro Convert."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MagewellApiError, MagewellClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONSECUTIVE_FAILURE_THRESHOLD = 5


class MagewellCoordinator(DataUpdateCoordinator):
    """Polls Magewell device for summary, channel, and NDI sources."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MagewellClient,
        scan_interval: int,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Magewell Pro Convert",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self._entry = entry
        self._consecutive_failures = 0

    async def _async_update_data(self) -> dict:
        """Fetch data from the device."""
        try:
            summary = await self.client.get_summary_info()
            channel = await self.client.get_channel()
            ndi_sources = await self.client.get_ndi_sources()
        except MagewellApiError as err:
            self._consecutive_failures += 1
            if self._consecutive_failures >= CONSECUTIVE_FAILURE_THRESHOLD:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    f"persistent_connection_failure_{self._entry.entry_id}",
                    is_fixable=False,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="persistent_connection_failure",
                    translation_placeholders={
                        "device": self._entry.title,
                        "count": str(self._consecutive_failures),
                    },
                )
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err

        if self._consecutive_failures >= CONSECUTIVE_FAILURE_THRESHOLD:
            ir.async_delete_issue(
                self.hass,
                DOMAIN,
                f"persistent_connection_failure_{self._entry.entry_id}",
            )
        self._consecutive_failures = 0

        return {
            "summary": summary,
            "channel": channel,
            "ndi_sources": ndi_sources,
        }
