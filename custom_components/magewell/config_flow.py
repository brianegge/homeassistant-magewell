"""Config flow for Magewell Pro Convert."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .api import MagewellAuthError, MagewellClient
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


class MagewellConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Magewell Pro Convert."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            client = MagewellClient(host, username, password)
            try:
                await client.login()
                await client.get_summary_info()
            except MagewellAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

            if not errors:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Magewell ({host})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        """Handle reauthentication when credentials become invalid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Handle reauth credential input."""
        errors = {}

        if user_input is not None:
            entry = self._get_reauth_entry()
            host = entry.data[CONF_HOST]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            client = MagewellClient(host, username, password)
            try:
                await client.login()
                await client.get_summary_info()
            except MagewellAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, **user_input},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration of the integration."""
        errors = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            host = user_input[CONF_HOST]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            client = MagewellClient(host, username, password)
            try:
                await client.login()
                await client.get_summary_info()
            except MagewellAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    title=f"Magewell ({host})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST, default=entry.data.get(CONF_HOST)
                    ): str,
                    vol.Required(
                        CONF_USERNAME,
                        default=entry.data.get(CONF_USERNAME, DEFAULT_USERNAME),
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
            errors=errors,
        )
