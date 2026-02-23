# Magewell Pro Convert for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for [Magewell Pro Convert](https://www.magewell.com/products/pro-convert) NDI decoders. Monitor device health, NDI connection state, and switch NDI inputs directly from the Home Assistant UI.

## Features

- **NDI Source Select** -- dropdown of discovered NDI sources on the network; selecting one switches the decoder's input
- **NDI Source sensor** -- currently active NDI source name with resolution and IP attributes
- **NDI Connected binary sensor** -- on/off connectivity status
- **Status sensor** -- device health (`ok`/`error`) with firmware and uptime attributes
- **CPU Usage / Core Temperature** -- diagnostic sensors for device health monitoring

All entities are grouped under a single HA device with model, firmware, serial number, and a link to the device's web UI.

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** > three-dot menu > **Custom repositories**
3. Add this repository URL and select **Integration** as the category
4. Search for and install **Magewell Pro Convert**
5. Restart Home Assistant

### Manual

Copy `custom_components/magewell/` into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **Magewell Pro Convert**
3. Enter the following:

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| Host | Yes | -- | IP address of your Magewell device |
| Username | No | `Admin` | Device username |
| Password | Yes | -- | Device password |
| Scan interval | No | `30` | Polling interval in seconds (10--300) |

## Entities

| Entity | Type | State | Attributes |
|--------|------|-------|------------|
| Status | `sensor` | `ok` / `error` | `device_name`, `firmware`, `uptime` |
| NDI Source | `sensor` | source name | `connected`, `video_resolution`, `ip_addr` |
| NDI Connected | `binary_sensor` | on / off | `ndi_source`, `video_resolution` |
| NDI Source Select | `select` | current source | options = discovered NDI sources |
| CPU Usage | `sensor` | percentage | *(diagnostic)* |
| Core Temperature | `sensor` | °C | *(diagnostic)* |

## How it works

The integration communicates with the Magewell device over its local HTTP API (`http://<host>/mwapi`). It authenticates with MD5-hashed credentials, maintains a persistent TCP session, and polls at the configured interval for device summary, current channel, and available NDI sources. No cloud services or external dependencies are required.

## Migration from shell script

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

MIT -- see [LICENSE](LICENSE) for details.
