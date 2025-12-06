"""Config flow for WeeChat Monitor integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_ENABLE_NOTIFICATIONS = True


class WeeChat_MonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WeeChat Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Check if already configured
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        # Check if WeeChat add-on is installed
        addon_info = await self._check_addon()
        addon_status = "not installed"
        if addon_info:
            addon_status = addon_info.get("state", "unknown")

        if user_input is not None:
            # Create the config entry
            return self.async_create_entry(
                title="WeeChat Monitor",
                data={},
                options={
                    "enable_notifications": user_input.get(
                        "enable_notifications", DEFAULT_ENABLE_NOTIFICATIONS
                    ),
                },
            )

        # Show the configuration form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "enable_notifications", default=DEFAULT_ENABLE_NOTIFICATIONS
                    ): selector.BooleanSelector(),
                }
            ),
            description_placeholders={
                "addon_status": addon_status,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> WeeChat_MonitorOptionsFlow:
        """Get the options flow for this handler."""
        return WeeChat_MonitorOptionsFlow(config_entry)

    async def _check_addon(self) -> dict[str, Any] | None:
        """Check if WeeChat add-on is installed."""
        try:
            # Check if supervisor is available
            if not self.hass.components.hassio.is_hassio():
                return None

            # Try to get add-on info
            # Replace 'local_weechat' with your actual add-on slug
            addon_slug = "local_weechat"
            addon_info = await self.hass.components.hassio.async_get_addon_info(
                addon_slug
            )
            return addon_info
        except Exception as e:
            _LOGGER.debug(f"Could not check add-on status: {e}")
            return None


class WeeChat_MonitorOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for WeeChat Monitor."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "enable_notifications",
                        default=self.config_entry.options.get(
                            "enable_notifications", DEFAULT_ENABLE_NOTIFICATIONS
                        ),
                    ): selector.BooleanSelector(),
                }
            ),
        )