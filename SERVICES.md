# Services — WeeChat Monitor Integration

This file documents the services exposed by the WeeChat Monitor integration and shows example payloads and how an add-on or script can call these services using Home Assistant's REST API.

## Overview
All services live under the `weechat` domain (per `const.py`). Services do not require `entity_id` — they operate on the integration's stored state.

Base REST endpoint for service calls:

POST /api/services/<domain>/<service>

Requests must include a valid Home Assistant access token (long-lived access token or an access token available to an add-on). Set header:

Authorization: Bearer <LONG_LIVED_ACCESS_TOKEN>
Content-Type: application/json

---

## 1) `weechat.register_download`
Register a completed DCC/XDCC download.

Path:

POST /api/services/weechat/register_download

Payload fields:
- `filename` (string, required): Name of the downloaded file (e.g., `video.mkv`).
- `size_bytes` (number, required): Size of the file in bytes.
- `timestamp` (number, optional): Unix timestamp of the download completion.
- `filename_suffix` (number, optional): Suffix appended to the filename in case of duplicates (e.g., `1` for `file.txt.1`).

Example (curl):

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_LONG_LIVED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "video.mkv", "size_bytes": 1073741824, "timestamp": 1700000000}' \
  https://<your-home-assistant>/api/services/weechat/register_download
```

Notes:
- If `timestamp` is omitted the integration will use the current UTC time.
- The integration will append the event to its recent history and update the relevant sensors.

---

## 2) `weechat.update_counts`
Update aggregated server/channel/chat counters. Intended to be called periodically by the WeeChat add-on to report current statistics.

Path:

POST /api/services/weechat/update_counts

Payload fields (all optional — include only fields you want to update):
- `total_servers` (number): Total number of known servers.
- `connected_servers` (number): Number of currently connected servers.
- `total_channels` (number): Total number of channels across servers.
- `total_private_chats` (number): Total number of private chats across servers.

Example (curl):

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_LONG_LIVED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"total_servers": 4, "connected_servers": 2, "total_channels": 37, "total_private_chats": 15}' \
  https://<your-home-assistant>/api/services/weechat/update_counts
```

Notes:
- Only fields provided in the JSON will be updated. The integration persists these counters in the same storage used for totals so values survive restarts.
- After a successful update the integration dispatches an update signal and the affected sensors will reflect the new values.

---

## Add-on integration recommendations
- Use a long-lived access token scoped to the add-on or a Home Assistant internal call if running inside the same environment.
- Call the `update_counts` periodically (for example every 30s–5min depending on how often you expect changes) or whenever the add-on detects a change in connections/channels.
- For download events, call `register_download` as soon as the transfer completes so counters and last-download details are accurate.

If you need help wiring the add-on to call these services, open an issue in this repository and include details about how the add-on is running (supervised, add-on, Docker, etc.).