"""Tests for the Magewell API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.magewell.api import (
    MagewellApiError,
    MagewellAuthError,
    MagewellClient,
)


@pytest.fixture
def client() -> MagewellClient:
    """Return a MagewellClient instance."""
    return MagewellClient("192.168.1.100", "Admin", "password")


def _mock_response(data: dict):
    """Create a mock aiohttp response context manager."""
    response = AsyncMock()
    response.json = AsyncMock(return_value=data)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=response)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


async def test_login_success(client: MagewellClient) -> None:
    """Test successful login."""
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(return_value=_mock_response({"status": 0}))
    client._session = mock_session
    client._logged_in = False

    await client.login()
    assert client._logged_in is True


async def test_login_auth_failure(client: MagewellClient) -> None:
    """Test login with wrong credentials raises MagewellAuthError."""
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(return_value=_mock_response({"status": -1}))
    client._session = mock_session
    client._logged_in = False

    with pytest.raises(MagewellAuthError, match="Login failed"):
        await client.login()
    assert client._logged_in is False


async def test_login_connection_error(client: MagewellClient) -> None:
    """Test login when device is unreachable."""
    mock_session = MagicMock()
    mock_session.closed = False
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection refused"))
    cm.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=cm)
    client._session = mock_session
    client._logged_in = False

    with pytest.raises(MagewellApiError, match="Cannot connect"):
        await client.login()
    assert client._logged_in is False


async def test_call_success(client: MagewellClient) -> None:
    """Test a successful API call."""
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(
        return_value=_mock_response({"status": 0, "data": "test"})
    )
    client._session = mock_session
    client._logged_in = True

    result = await client.get_summary_info()
    assert result == {"status": 0, "data": "test"}


async def test_call_relogin_on_session_expiry(client: MagewellClient) -> None:
    """Test automatic re-login when session expires."""
    expired_resp = _mock_response({"status": -1})
    success_resp = _mock_response({"status": 0, "data": "ok"})
    login_resp = _mock_response({"status": 0})

    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # 1st call: expired summary, 2nd call: login, 3rd call: retry summary
        if call_count == 1:
            return expired_resp
        elif call_count == 2:
            return login_resp
        else:
            return success_resp

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(side_effect=side_effect)
    client._session = mock_session
    client._logged_in = True

    result = await client.get_summary_info()
    assert result == {"status": 0, "data": "ok"}
    assert call_count == 3


async def test_call_connection_error(client: MagewellClient) -> None:
    """Test API call with connection error."""
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("timeout"))
    cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(return_value=cm)
    client._session = mock_session
    client._logged_in = True

    with pytest.raises(MagewellApiError, match="failed"):
        await client.get_summary_info()


async def test_get_ndi_sources(client: MagewellClient) -> None:
    """Test get_ndi_sources extracts source names."""
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(
        return_value=_mock_response({
            "status": 0,
            "sources": [
                {"name": "Camera 1"},
                {"name": "Camera 2"},
                {"other": "no name key"},
            ],
        })
    )
    client._session = mock_session
    client._logged_in = True

    result = await client.get_ndi_sources()
    assert result == ["Camera 1", "Camera 2"]


async def test_set_channel(client: MagewellClient) -> None:
    """Test set_channel sends the correct ndi-name parameter."""
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(
        return_value=_mock_response({"status": 0})
    )
    client._session = mock_session
    client._logged_in = True

    await client.set_channel("Camera 2")

    call_kwargs = mock_session.get.call_args
    assert call_kwargs[1]["params"]["ndi-name"] == "Camera 2"


async def test_list_channels(client: MagewellClient) -> None:
    """Test list_channels returns channel list."""
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(
        return_value=_mock_response({
            "status": 0,
            "channels": [{"name": "preset1"}, {"name": "preset2"}],
        })
    )
    client._session = mock_session
    client._logged_in = True

    result = await client.list_channels()
    assert result == [{"name": "preset1"}, {"name": "preset2"}]


async def test_close(client: MagewellClient) -> None:
    """Test close cleans up session and connector."""
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.close = AsyncMock()
    mock_connector = MagicMock()
    mock_connector.closed = False
    mock_connector.close = AsyncMock()

    client._session = mock_session
    client._connector = mock_connector
    client._logged_in = True

    await client.close()

    mock_session.close.assert_awaited_once()
    mock_connector.close.assert_awaited_once()
    assert client._session is None
    assert client._connector is None
    assert client._logged_in is False


async def test_close_already_closed(client: MagewellClient) -> None:
    """Test close when session is already closed."""
    client._session = None
    client._connector = None

    # Should not raise
    await client.close()


async def test_ensure_session_creates_new(client: MagewellClient) -> None:
    """Test _ensure_session creates a new session when none exists."""
    assert client._session is None

    with patch("aiohttp.TCPConnector") as mock_connector_cls, \
         patch("aiohttp.ClientSession") as mock_session_cls:
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session_cls.return_value = mock_session

        session = client._ensure_session()

        assert session is mock_session
        assert client._logged_in is False
        mock_connector_cls.assert_called_once()


async def test_call_auto_login_when_not_logged_in(client: MagewellClient) -> None:
    """Test _call automatically logs in if not logged in."""
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # login response
            return _mock_response({"status": 0})
        else:
            # actual API call response
            return _mock_response({"status": 0, "result": "data"})

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(side_effect=side_effect)
    client._session = mock_session
    client._logged_in = False

    result = await client.get_channel()
    assert result == {"status": 0, "result": "data"}
    assert call_count == 2  # login + get-channel
