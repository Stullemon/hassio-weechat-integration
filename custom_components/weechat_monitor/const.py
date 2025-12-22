"""Constants for the WeeChat Monitor integration."""
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "weechat_monitor"
PLATFORMS: list[Platform] = [Platform.SENSOR]