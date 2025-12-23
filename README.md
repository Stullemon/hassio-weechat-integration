# hassio-weechat-integration

Lightweight Home Assistant custom integration to monitor downloads and metrics from a WeeChat instance (via the WeeChat add-on).

---

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [HACS (recommended)](#hacs-recommended)
  - [Manual installation](#manual-installation)
- [Configuration](#configuration)
- [Entities](#entities)
- [Services](#services)
- [Usage examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Development & Contributing](#development--contributing)
- [License](#license)
- [Disclaimer](#disclaimer)

---

## Features
- Exposes download statistics as Home Assistant sensors (daily and total counts/volumes).
- Records information about the last download (filename, size, timestamp, humanized "time ago").
- Provides a service to register downloads from external sources (e.g., WeeChat DCC events).
- Simple configuration flow and built-in translations.

## Requirements
- Home Assistant core (tested on recent versions; compatibility may vary).
- A running WeeChat add-on or another process capable of calling the integration's service(s).

---

## Installation

### HACS (recommended)
1. Ensure HACS is installed in your Home Assistant instance.
2. In HACS, go to **Integrations → ⋯ → Custom repositories**.
3. Add this repository URL and select **Category: Integration**.
4. After installation, go to **Settings → Devices & Services → Add Integration** and search for "Weechat Monitor".

See HACS docs for publishing & installing integrations: https://www.hacs.xyz/docs/publish/integration/

### Manual installation
1. Copy the `weechat_monitor` folder to your Home Assistant `custom_components/` directory:

```text
<config_dir>/custom_components/weechat_monitor/
```

2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**, search for "Weechat Monitor" and complete the setup.

---

## Configuration
Configuration is handled through the Home Assistant UI (integration setup). No YAML configuration is required for the default setup.

After adding the integration, Home Assistant will create a device named **WeeChat Monitor** and the sensors listed below.

---

## Entities
The integration exposes the following sensors (entity names shown are examples — actual entity IDs are based on the integration instance and unique IDs):

- **sensor.daily_downloads** — Daily Downloads
  - state: number of downloads today
  - attributes: `last_reset` (ISO datetime), `recent_history` (number of recent items stored)

- **sensor.daily_download_volume** — Daily Download Volume
  - state: bytes downloaded today (suggested display in GB)
  - attributes: `bytes`, `formatted`, `last_reset`

- **sensor.total_downloads** — Total Downloads
  - state: total downloads (all time)

- **sensor.total_download_volume** — Total Download Volume
  - state: total bytes downloaded (all time)
  - attributes: `bytes`, `formatted`

- **sensor.last_download** — Last Download
  - state: filename (or "No downloads yet")
  - attributes: `filename`, `size_bytes`, `size_formatted`, `timestamp`, `time_ago`

- **sensor.total_servers** — Total Servers
  - state: total known servers

- **sensor.connected_servers** — Connected Servers
  - state: number of currently connected servers

- **sensor.total_channels** — Total Channels
  - state: total channels across all servers

- **sensor.total_private_chats** — Total Private Chats
  - state: total private chats across all servers

> Note: actual entity IDs will include the integration entry ID and may be shown in the UI with the friendly names above.

---

## Services
This integration provides the following services to interact with the integration. A dedicated `SERVICES.md` file explains the exact payloads and provides examples for calling the Home Assistant services via the REST API (use an access token or call from an add-on running inside Home Assistant): `SERVICES.md`.

### `weechat.register_download`
Registers a completed DCC download. Useful to be called from an external script, an add-on, or from an automation triggered by the WeeChat add-on.

Fields:
- `filename` (string, required): Name of the downloaded file (e.g., `video.mkv`).
- `size_bytes` (number, required): Size of the file in bytes.
- `timestamp` (number, optional): Unix timestamp of the download completion.
- `filename_suffix` (number, optional): Suffix appended to the filename in case of duplicates (e.g., `1` for `file.txt.1`).

Example service call (YAML):

```yaml
service: weechat.register_download
data:
  filename: "video.mkv"
  size_bytes: 1073741824
  timestamp: 1700000000
```

---

### `weechat.update_counts`
Update aggregated counters (servers, channels, private chats) — intended to be called periodically by the WeeChat add-on.

Fields:
- `total_servers` (number, optional): Total number of known servers.
- `connected_servers` (number, optional): Number of currently connected servers.
- `total_channels` (number, optional): Total number of channels.
- `total_private_chats` (number, optional): Total number of private chats.

Example service call (YAML):

```yaml
service: weechat.update_counts
data:
  total_servers: 4
  connected_servers: 2
  total_channels: 37
  total_private_chats: 15
```

For full examples (curl / REST) and details for add-on authors, see `SERVICES.md`. 
---

## Usage examples
- Add the sensors to a Lovelace dashboard to display current download activity and total usage.
- Create automations that trigger when `sensor.last_download` changes or when `sensor.daily_download_volume` exceeds a threshold.
- Use the `register_download` service to record downloads from external scripts or add-ons.

Example automation snippet (notify on large downloads):

```yaml
trigger:
  - platform: state
    entity_id: sensor.last_download
condition:
  - condition: numeric_state
    entity_id: sensor.last_download
    value_template: "{{ state_attr('sensor.last_download', 'size_bytes') | int > 1073741824 }}"
action:
  - service: notify.mobile_app
    data:
      message: "Large file downloaded: {{ trigger.to_state.state }}"
```

---

## Troubleshooting
- Integration not visible after install: restart Home Assistant and check Logs for errors.
- Sensors show unexpected values: confirm the WeeChat add-on (or the system calling `register_download`) is correctly sending data.
- For more details, enable debug logging for `weechat_monitor` in Home Assistant's logger.

---

## Development & Contributing
Contributions are welcome! Suggested workflow:
1. Fork the repository and create a feature branch.
2. Add tests and documentation for changes where applicable.
3. Open a pull request with a clear description of the change.

If you're uncertain, open an issue to discuss proposed changes first.

---

## License
This project is licensed under the MIT License — see the `LICENSE` file for full details.

---

## Disclaimer
- **Not affiliated with WeeChat:** This project is **in no way related to the WeeChat project** or its maintainers.
- **Provided as-is:** The software is provided **"as is"**, without warranty of any kind. Use at your own risk.

If you need help integrating this into your Home Assistant instance, please open an issue.
