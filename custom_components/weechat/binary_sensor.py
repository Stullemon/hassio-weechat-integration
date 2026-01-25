"""WeeChat Monitor Binary Sensors."""
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    _LOGGER.info("Setting up WeeChat Monitor binary sensors")

    async_add_entities([WeeChat_AddonAliveSensor(hass, entry)], True)


class WeeChat_AddonAliveSensor(BinarySensorEntity):
    """Binary sensor indicating whether the WeeChat add-on is alive."""

    _attr_has_entity_name = True
    _attr_name = "Addon Alive"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_addon_alive"
        self._is_on = False
        self._last_seen = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WeeChat Monitor",
            manufacturer="Custom",
            model="WeeChat Addon",
            sw_version="0.1.0",
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks and initialize state from hass.data."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, f"{DOMAIN}_update", self._handle_update)
        )
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._is_on = bool(data.get("addon_alive", False))
        self._last_seen = data.get("last_seen")

    @callback
    def _handle_update(self) -> None:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._is_on = bool(data.get("addon_alive", False))
        self._last_seen = data.get("last_seen")
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "last_seen": self._last_seen,
        }