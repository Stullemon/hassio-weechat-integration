"""WeeChat Monitor Integration for Home Assistant."""
import logging
from datetime import datetime, timedelta
from typing import Final

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.const import Platform
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

DOMAIN: Final = "weechat_monitor"
PLATFORMS: list[Platform] = [Platform.SENSOR]
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.storage"

# Storage for download data
DOWNLOAD_DATA = {
    "downloads": [],  # List of recent downloads (for display)
    "daily_count": 0,
    "daily_bytes": 0,
    "last_reset": datetime.now().date(),
    "last_download": None,
    "total_count": 0,  # Persistent total
    "total_bytes": 0,  # Persistent total
}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WeeChat Monitor integration from YAML (legacy)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WeeChat Monitor from a config entry."""
    _LOGGER.info("Setting up WeeChat Monitor integration")
    
    # Check if WeeChat add-on is available
    addon_available = await _check_addon_available(hass)
    if addon_available:
        _LOGGER.info("WeeChat add-on detected and running")
    else:
        _LOGGER.warning("WeeChat add-on not detected - integration will still work if called manually")
    
    # Initialize domain data
    hass.data.setdefault(DOMAIN, {})
    
    # Create storage handler
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    
    # Load persisted data
    stored_data = await store.async_load()
    if stored_data:
        _LOGGER.info(f"Loaded persisted data: {stored_data.get('total_count', 0)} downloads, {stored_data.get('total_bytes', 0)} bytes")
        data = DOWNLOAD_DATA.copy()
        data.update({
            "total_count": stored_data.get("total_count", 0),
            "total_bytes": stored_data.get("total_bytes", 0),
            "last_download": stored_data.get("last_download"),
        })
        # Reset daily counters if date changed
        last_reset_str = stored_data.get("last_reset")
        if last_reset_str:
            last_reset = datetime.fromisoformat(last_reset_str).date()
            if last_reset == datetime.now().date():
                data["daily_count"] = stored_data.get("daily_count", 0)
                data["daily_bytes"] = stored_data.get("daily_bytes", 0)
                data["last_reset"] = last_reset
        hass.data[DOMAIN][entry.entry_id] = data
    else:
        hass.data[DOMAIN][entry.entry_id] = DOWNLOAD_DATA.copy()
    
    hass.data[DOMAIN]["store"] = store
    
    async def save_data():
        """Save data to storage."""
        data = hass.data[DOMAIN][entry.entry_id]
        await store.async_save({
            "total_count": data["total_count"],
            "total_bytes": data["total_bytes"],
            "daily_count": data["daily_count"],
            "daily_bytes": data["daily_bytes"],
            "last_reset": data["last_reset"].isoformat(),
            "last_download": data["last_download"],
        })
    
    async def handle_register_download(call: ServiceCall) -> None:
        """Handle download registration from WeeChat."""
        filename = call.data.get("filename")
        size_bytes = call.data.get("size_bytes", 0)
        timestamp = call.data.get("timestamp")
        filename_suffix = call.data.get("filename_suffix", -1)
        display_filename = filename
        if filename_suffix > 0:
            display_filename = f"{filename}.{filename_suffix}"
        
        if timestamp:
            download_time = dt_util.utc_from_timestamp(float(timestamp))
        else:
            download_time = dt_util.utcnow()
        
        _LOGGER.info(f"Registered download: {filename} ({size_bytes} bytes)")
        
        # Get the first entry's data (we only support one instance)
        entry_id = list(filter(lambda k: k != "store", hass.data[DOMAIN].keys()))[0]
        data = hass.data[DOMAIN][entry_id]
        
        # Check if we need to reset daily counters
        today = datetime.now().date()
        if data["last_reset"] != today:
            _LOGGER.info("Resetting daily counters")
            data["daily_count"] = 0
            data["daily_bytes"] = 0
            data["last_reset"] = today
        
        # Update daily data
        data["daily_count"] += 1
        data["daily_bytes"] += size_bytes
        
        # Update total data (persistent)
        data["total_count"] += 1
        data["total_bytes"] += size_bytes
        
        data["last_download"] = {
            "filename": display_filename,
            "size_bytes": size_bytes,
            "timestamp": download_time.isoformat(),
        }
        
        # Store in recent history (keep last 50 for display)
        data["downloads"].append({
            "filename": filename,
            "size_bytes": size_bytes,
            "timestamp": download_time.isoformat(),
        })
        if len(data["downloads"]) > 50:
            data["downloads"] = data["downloads"][-50:]
        
        # Save to persistent storage
        await save_data()
        
        # Send notification if enabled
        downloaded_tag = "Downloaded"
        if filename_suffix > 0:
            downloaded_tag = "Downloaded (duplicate)"
        if entry.options.get("enable_notifications", True):
            await hass.services.async_call(
                "notify",
                "persistent_notification",
                {
                    "title": "WeeChat Download Complete",
                    "message": f"{downloaded_tag}: {display_filename}\nSize: {_format_bytes(size_bytes)}",
                },
            )
        
        # Update sensors
        async_dispatcher_send(hass, f"{DOMAIN}_update")
    
    # Register service
    hass.services.async_register(
        DOMAIN, "register_download", handle_register_download
    )
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Daily reset task
    async def daily_reset(now):
        """Reset daily counters at midnight."""
        today = datetime.now().date()
        for entry_id, data in hass.data[DOMAIN].items():
            if entry_id == "store":
                continue
            if isinstance(data, dict) and data.get("last_reset") != today:
                _LOGGER.info("Daily reset triggered")
                data["daily_count"] = 0
                data["daily_bytes"] = 0
                data["last_reset"] = today
                await save_data()
                async_dispatcher_send(hass, f"{DOMAIN}_update")
    
    async_track_time_interval(hass, daily_reset, timedelta(hours=1))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Save data before unloading
    store = hass.data[DOMAIN].get("store")
    if store:
        data = hass.data[DOMAIN][entry.entry_id]
        await store.async_save({
            "total_count": data["total_count"],
            "total_bytes": data["total_bytes"],
            "daily_count": data["daily_count"],
            "daily_bytes": data["daily_bytes"],
            "last_reset": data["last_reset"].isoformat(),
            "last_download": data["last_download"],
        })
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def _check_addon_available(hass: HomeAssistant) -> bool:
    """Check if WeeChat add-on is installed and running."""
    try:
        # Check if supervisor is available
        if not hass.components.hassio.is_hassio():
            return False

        # Try to get add-on info
        # Replace 'local_weechat' with your actual add-on slug
        addon_slug = "local_weechat"
        addon_info = await hass.components.hassio.async_get_addon_info(addon_slug)
        
        if addon_info and addon_info.get("state") == "started":
            return True
    except Exception as e:
        _LOGGER.debug(f"Could not check add-on status: {e}")
    
    return False


def _format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"