"""DataUpdateCoordinator for Magewell Pro Convert."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MagewellApiError, MagewellClient

_LOGGER = logging.getLogger(__name__)


class MagewellCoordinator(DataUpdateCoordinator):
    """Polls Magewell device for summary, channel, and NDI sources."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MagewellClient,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Magewell Pro Convert",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch data from the device."""
        try:
            summary = await self.client.get_summary_info()
            channel = await self.client.get_channel()
            ndi_sources = await self.client.get_ndi_sources()
        except MagewellApiError as err:
            raise UpdateFailed(f"Error communicating with Magewell: {err}") from err

        return {
            "summary": summary,
            "channel": channel,
            "ndi_sources": ndi_sources,
        }
