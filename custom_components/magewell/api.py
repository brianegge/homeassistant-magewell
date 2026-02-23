"""Async HTTP client for Magewell Pro Convert devices."""

import hashlib
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class MagewellApiError(Exception):
    """Base exception for Magewell API errors."""


class MagewellAuthError(MagewellApiError):
    """Authentication failed."""


class MagewellClient:
    """Async client for Magewell Pro Convert HTTP API."""

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize the client."""
        self._host = host
        self._username = username
        self._password_md5 = hashlib.md5(password.encode()).hexdigest()
        self._base_url = f"http://{host}/mwapi"
        self._session: aiohttp.ClientSession | None = None
        self._connector: aiohttp.TCPConnector | None = None
        self._logged_in = False

    def _ensure_session(self) -> aiohttp.ClientSession:
        """Create session if needed."""
        if self._session is None or self._session.closed:
            self._connector = aiohttp.TCPConnector(
                keepalive_timeout=300,
                enable_cleanup_closed=True,
            )
            jar = aiohttp.CookieJar(unsafe=True)
            self._session = aiohttp.ClientSession(
                connector=self._connector, cookie_jar=jar
            )
            self._logged_in = False
        return self._session

    async def login(self) -> None:
        """Authenticate with the device."""
        session = self._ensure_session()
        try:
            async with session.get(
                self._base_url,
                params={
                    "method": "login",
                    "id": self._username,
                    "pass": self._password_md5,
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            self._logged_in = False
            raise MagewellApiError(f"Cannot connect to {self._host}: {err}") from err

        if data.get("status") != 0:
            self._logged_in = False
            raise MagewellAuthError(
                f"Login failed (status={data.get('status')})"
            )

        self._logged_in = True
        _LOGGER.debug("Logged in to Magewell at %s", self._host)

    async def _call(self, method: str, **params: Any) -> dict:
        """Call an API method, re-logging in on session expiry."""
        session = self._ensure_session()

        if not self._logged_in:
            await self.login()

        query = {"method": method, **params}
        try:
            async with session.get(
                self._base_url,
                params=query,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise MagewellApiError(
                f"API call {method} failed: {err}"
            ) from err

        # Re-login once on session expiry (status -1 or missing)
        status = data.get("status", -1)
        if status != 0 and self._logged_in:
            _LOGGER.debug("Session expired, re-logging in")
            self._logged_in = False
            await self.login()
            try:
                async with session.get(
                    self._base_url,
                    params=query,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    data = await resp.json(content_type=None)
            except (aiohttp.ClientError, TimeoutError) as err:
                raise MagewellApiError(
                    f"API call {method} failed after re-login: {err}"
                ) from err

            if data.get("status") != 0:
                raise MagewellApiError(
                    f"API call {method} returned status {data.get('status')}"
                )

        return data

    async def get_summary_info(self) -> dict:
        """Get device summary (NDI status, video stats, CPU, temp)."""
        return await self._call("get-summary-info")

    async def get_ndi_sources(self) -> list[str]:
        """Get list of discovered NDI sources on the network."""
        data = await self._call("get-ndi-sources")
        sources = data.get("sources", [])
        return [s["name"] for s in sources if "name" in s]

    async def get_channel(self) -> dict:
        """Get the current active channel/source."""
        return await self._call("get-channel")

    async def set_channel(self, ndi_name: str) -> dict:
        """Switch the decoder to a different NDI source."""
        return await self._call("set-channel", **{"ndi-name": ndi_name})

    async def list_channels(self) -> list[dict]:
        """List saved preset channels."""
        data = await self._call("list-channels")
        return data.get("channels", [])

    async def close(self) -> None:
        """Close the HTTP session and connector."""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector and not self._connector.closed:
            await self._connector.close()
        self._session = None
        self._connector = None
        self._logged_in = False
