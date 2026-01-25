"""Config flow for WeeChat Monitor integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import DOMAIN

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
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> WeeChat_MonitorOptionsFlow:
        """Get the options flow for this handler."""
        return WeeChat_MonitorOptionsFlow()


class WeeChat_MonitorOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for WeeChat Monitor."""

    def __init__(self) -> None:
        """Initialize options flow."""

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