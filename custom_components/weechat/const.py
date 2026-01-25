"""Constants for the WeeChat Monitor integration."""
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "weechat"
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]