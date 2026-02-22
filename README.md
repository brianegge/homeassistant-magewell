# Magewell Pro Convert for Home Assistant

A Home Assistant custom integration for [Magewell Pro Convert](https://www.magewell.com/products/pro-convert) NDI decoders. Exposes device status, NDI connection state, and an NDI source selector that lets you switch inputs from the HA UI.

## Features

- **NDI Source Select** — dropdown of discovered NDI sources on the network; selecting one switches the decoder's input via the `set-channel` API
- **NDI Source sensor** — shows the currently active NDI source name
- **NDI Connected binary sensor** — on/off connectivity status
- **Status sensor** — device health (ok/error) with firmware and uptime attributes
- **CPU Usage / Core Temperature** — diagnostic sensors

All entities are grouped under a single HA Device with model, firmware, serial number, and a link to the device's web UI.

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** > **Custom repositories**
3. Add this repository URL and select **Integration** as the category
4. Install **Magewell Pro Convert**
5. Restart Home Assistant

### Manual

Copy `custom_components/magewell/` to your Home Assistant `custom_components` directory and restart.

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **Magewell Pro Convert**
3. Enter:
   - **Host** — IP address of your Magewell device (e.g. `192.168.3.15`)
   - **Username** — device username (default: `Admin`)
   - **Password** — device password
   - **Scan interval** — polling interval in seconds (default: 30, range: 10–300)

## Entities

| Entity | Type | State | Attributes |
|--------|------|-------|------------|
| Status | sensor | `ok` / `error` | device_name, firmware, uptime |
| NDI Source | sensor | source name | connected, video_resolution, ip_addr |
| NDI Connected | binary_sensor | on/off | ndi_source, video_resolution |
| NDI Source Select | select | current source | options = discovered NDI sources |
| CPU Usage | sensor | percentage | *(diagnostic)* |
| Core Temperature | sensor | °C | *(diagnostic)* |

## Migration from Shell Script

If you previously used the `magewell_status.sh` + `command_line` sensor approach:

1. Install this integration via HACS or manually
2. Restart Home Assistant and add the integration via the UI
3. Remove from `configuration.yaml`:
   - The `command_line` sensor for Magewell Status
   - The `template` binary sensor for Magewell NDI Connected
   - The `template` sensor for Magewell NDI Source
4. Delete `scripts/magewell_status.sh`
5. Restart Home Assistant
6. Update any dashboard cards or automations to use the new entity IDs

## License

MIT
