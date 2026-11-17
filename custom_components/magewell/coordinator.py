"""DataUpdateCoordinator for Magewell Pro Convert."""

import inspect
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

# HA 2026.11 lets a repair issue belong to a config entry, so it is deleted
# along with the entry. Older releases (hacs.json allows 2024.1+) reject the
# keyword, so only pass it where async_create_issue accepts it.
ISSUE_SUPPORTS_CONFIG_ENTRY = "config_entry_id" in inspect.signature(ir.async_create_issue).parameters


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
                issue_kwargs = {}
                if ISSUE_SUPPORTS_CONFIG_ENTRY:
                    issue_kwargs["config_entry_id"] = self._entry.entry_id
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
                    **issue_kwargs,
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
