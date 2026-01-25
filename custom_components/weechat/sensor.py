"""WeeChat Monitor Sensors."""
import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
    RestoreEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation
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
    """Set up WeeChat Monitor sensors from config entry."""
    _LOGGER.info("Setting up WeeChat Monitor sensors")
    
    sensors = [
        WeeChat_DailyCountSensor(hass, entry),
        WeeChat_DailyBytesSensor(hass, entry),
        WeeChat_TotalCountSensor(hass, entry),
        WeeChat_TotalBytesSensor(hass, entry),
        WeeChat_LastDownloadSensor(hass, entry),
        WeeChat_TotalServersSensor(hass, entry),
        WeeChat_ConnectedServersSensor(hass, entry),
        WeeChat_TotalChannelsSensor(hass, entry),
        WeeChat_TotalPrivateChatsSensor(hass, entry),
    ]
    
    async_add_entities(sensors, True)


class WeeChat_DailyCountSensor(SensorEntity):
    """Sensor for daily download count."""
    
    _attr_has_entity_name = True
    _attr_name = "Daily Downloads"
    _attr_icon = "mdi:download-multiple"
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "downloads"
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_daily_count"
        self._attr_native_value = 0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WeeChat Monitor",
            manufacturer="Custom",
            model="Download Monitor",
            sw_version="0.1.0",
        )
    
    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._handle_update
            )
        )
    
    @callback
    def _handle_update(self) -> None:
        """Handle updated data."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data["daily_count"]
        self.async_write_ha_state()
    
    async def async_update(self) -> None:
        """Update sensor."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data["daily_count"]
    
    @property
    def last_reset(self):
        """Return the time when the sensor was last reset."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        return dt_util.start_of_local_day(
            dt_util.as_local(dt_util.now())
        ).replace(
            year=data["last_reset"].year,
            month=data["last_reset"].month,
            day=data["last_reset"].day
        )
        
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        return {
            "last_reset": data["last_reset"].isoformat(),
            "recent_history": len(data["downloads"]),
        }


class WeeChat_DailyBytesSensor(SensorEntity):
    """Sensor for daily download volume."""
    
    _attr_has_entity_name = True
    _attr_name = "Daily Download Volume"
    _attr_icon = "mdi:database-arrow-down"
    _attr_state_class = SensorStateClass.TOTAL
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = UnitOfInformation.BYTES
    _attr_suggested_unit_of_measurement = UnitOfInformation.GIGABYTES
    _attr_suggested_display_precision = 2
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_daily_bytes"
        self._attr_native_value = 0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WeeChat Monitor",
            manufacturer="Custom",
            model="Download Monitor",
            sw_version="0.1.0",
        )
    
    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._handle_update
            )
        )
    
    @callback
    def _handle_update(self) -> None:
        """Handle updated data."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data["daily_bytes"]
        self.async_write_ha_state()
    
    async def async_update(self) -> None:
        """Update sensor."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data["daily_bytes"]
    
    @property
    def last_reset(self):
        """Return the time when the sensor was last reset."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        return dt_util.start_of_local_day(
            dt_util.as_local(dt_util.now())
        ).replace(
            year=data["last_reset"].year,
            month=data["last_reset"].month,
            day=data["last_reset"].day
        )
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        bytes_val = data["daily_bytes"]
        return {
            "bytes": bytes_val,
            "formatted": self._format_bytes(bytes_val),
            "last_reset": data["last_reset"].isoformat(),
        }
    
    @staticmethod
    def _format_bytes(bytes_val: int) -> str:
        """Format bytes."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"


class WeeChat_TotalCountSensor(RestoreEntity, SensorEntity):
    """Sensor for total download count (all time)."""
    
    _attr_has_entity_name = True
    _attr_name = "Total Downloads"
    _attr_icon = "mdi:download-box"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "downloads"
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_total_count"
        self._attr_native_value = 0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WeeChat Monitor",
            manufacturer="Custom",
            model="Download Monitor",
            sw_version="0.1.0",
        )
    
    async def async_added_to_hass(self) -> None:
        """Register callbacks and restore state."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._handle_update
            )
        )
        
        # Load from memory (already restored from storage)
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data["total_count"]
    
    @callback
    def _handle_update(self) -> None:
        """Handle updated data."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data["total_count"]
        self.async_write_ha_state()
    
    async def async_update(self) -> None:
        """Update sensor."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data["total_count"]


class WeeChat_TotalBytesSensor(RestoreEntity, SensorEntity):
    """Sensor for total download volume (all time)."""
    
    _attr_has_entity_name = True
    _attr_name = "Total Download Volume"
    _attr_icon = "mdi:database"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = UnitOfInformation.BYTES
    _attr_suggested_unit_of_measurement = UnitOfInformation.GIGABYTES
    _attr_suggested_display_precision = 2
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_total_bytes"
        self._attr_native_value = 0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WeeChat Monitor",
            manufacturer="Custom",
            model="Download Monitor",
            sw_version="0.1.0",
        )
    
    async def async_added_to_hass(self) -> None:
        """Register callbacks and restore state."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._handle_update
            )
        )
        
        # Load from memory (already restored from storage)
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data["total_bytes"]
    
    @callback
    def _handle_update(self) -> None:
        """Handle updated data."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data["total_bytes"]
        self.async_write_ha_state()
    
    async def async_update(self) -> None:
        """Update sensor."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data["total_bytes"]
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        bytes_val = data["total_bytes"]
        return {
            "bytes": bytes_val,
            "formatted": self._format_bytes(bytes_val),
        }
    
    @staticmethod
    def _format_bytes(bytes_val: int) -> str:
        """Format bytes."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"


class WeeChat_LastDownloadSensor(SensorEntity):
    """Sensor for last download info."""
    
    _attr_has_entity_name = True
    _attr_name = "Last Download"
    _attr_icon = "mdi:download"
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_download"
        self._attr_native_value = "No downloads yet"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WeeChat Monitor",
            manufacturer="Custom",
            model="Download Monitor",
            sw_version="0.1.0",
        )
    
    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._handle_update
            )
        )
        # Set initial value
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        last = data.get("last_download")
        if last:
            self._attr_native_value = last["filename"]
    
    @callback
    def _handle_update(self) -> None:
        """Handle updated data."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        last = data["last_download"]
        if last:
            self._attr_native_value = last["filename"]
        self.async_write_ha_state()
    
    async def async_update(self) -> None:
        """Update sensor."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        last = data["last_download"]
        if last:
            self._attr_native_value = last["filename"]
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        last = data["last_download"]
        if not last:
            return {}
        
        timestamp_str = last["timestamp"]
        if isinstance(timestamp_str, str):
            timestamp = dt_util.parse_datetime(timestamp_str)
        else:
            timestamp = timestamp_str
        
        return {
            "filename": last["filename"],
            "size_bytes": last["size_bytes"],
            "size_formatted": self._format_bytes(last["size_bytes"]),
            "timestamp": timestamp_str if isinstance(timestamp_str, str) else timestamp.isoformat(),
            "time_ago": self._time_ago(timestamp) if timestamp else "Unknown",
        }
    
    @staticmethod
    def _format_bytes(bytes_val: int) -> str:
        """Format bytes."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"
    
    @staticmethod
    def _time_ago(timestamp: datetime) -> str:
        """Format time ago."""
        if not timestamp:
            return "Unknown"
            
        delta = dt_util.utcnow() - dt_util.as_utc(timestamp)
        
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
        
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        
        minutes = delta.seconds // 60
        if minutes > 0:
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        
        return "Just now"

class WeeChat_TotalServersSensor(RestoreEntity, SensorEntity):
    """Sensor for total servers known."""

    _attr_has_entity_name = True
    _attr_name = "Total Servers"
    _attr_icon = "mdi:server"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "servers"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_total_servers"
        self._attr_native_value = 0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WeeChat Monitor",
            manufacturer="Custom",
            model="Server Stats",
            sw_version="0.1.0",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._handle_update
            )
        )
        # Initialize from hass.data
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("total_servers", 0)

    @callback
    def _handle_update(self) -> None:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("total_servers", 0)
        self.async_write_ha_state()

    async def async_update(self) -> None:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("total_servers", 0)


class WeeChat_ConnectedServersSensor(RestoreEntity, SensorEntity):
    """Sensor for currently connected servers."""

    _attr_has_entity_name = True
    _attr_name = "Connected Servers"
    _attr_icon = "mdi:server-network"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "servers"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_connected_servers"
        self._attr_native_value = 0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WeeChat Monitor",
            manufacturer="Custom",
            model="Server Stats",
            sw_version="0.1.0",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._handle_update
            )
        )
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("connected_servers", 0)

    @callback
    def _handle_update(self) -> None:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("connected_servers", 0)
        self.async_write_ha_state()

    async def async_update(self) -> None:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("connected_servers", 0)


class WeeChat_TotalChannelsSensor(RestoreEntity, SensorEntity):
    """Sensor for total channels across servers."""

    _attr_has_entity_name = True
    _attr_name = "Total Channels"
    _attr_icon = "mdi:chat"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "channels"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_total_channels"
        self._attr_native_value = 0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WeeChat Monitor",
            manufacturer="Custom",
            model="Channel Stats",
            sw_version="0.1.0",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._handle_update
            )
        )
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("total_channels", 0)

    @callback
    def _handle_update(self) -> None:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("total_channels", 0)
        self.async_write_ha_state()

    async def async_update(self) -> None:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("total_channels", 0)


class WeeChat_TotalPrivateChatsSensor(RestoreEntity, SensorEntity):
    """Sensor for total private chats."""

    _attr_has_entity_name = True
    _attr_name = "Total Private Chats"
    _attr_icon = "mdi:account-multiple"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "chats"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_total_private_chats"
        self._attr_native_value = 0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WeeChat Monitor",
            manufacturer="Custom",
            model="Channel Stats",
            sw_version="0.1.0",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self._handle_update
            )
        )
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("total_private_chats", 0)

    @callback
    def _handle_update(self) -> None:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("total_private_chats", 0)
        self.async_write_ha_state()

    async def async_update(self) -> None:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        self._attr_native_value = data.get("total_private_chats", 0)
