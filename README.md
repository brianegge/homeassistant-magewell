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

## Data updates

The integration polls the Magewell device over its local HTTP API (`http://<host>/mwapi`) at the configured scan interval (default: 30 seconds, range: 10--300 seconds). Each poll fetches three endpoints: device summary (status, CPU, temperature, NDI state), current channel, and discovered NDI sources. Authentication uses MD5-hashed credentials over a persistent TCP connection. All communication is local; no cloud services or external dependencies are required.

## Supported devices

- **Magewell Pro Convert** NDI decoder family, including:
  - Pro Convert for NDI to HDMI
  - Pro Convert for NDI to SDI
  - Pro Convert for NDI to HDMI 4K
  - Pro Convert for NDI to AIO
- Any Magewell device exposing the `/mwapi` HTTP management API with firmware supporting `get-summary-info`, `get-channel`, `get-ndi-sources`, and `set-channel` methods.

## Known limitations

- **No auto-discovery**: Magewell devices do not advertise via SSDP, Zeroconf, or DHCP, so the device IP must be entered manually.
- **HTTP only**: The device API does not support HTTPS. Credentials are sent as MD5 hashes, not plaintext, but traffic is unencrypted.
- **Single session**: The device supports a limited number of concurrent HTTP sessions. If you have the web UI open, polling may occasionally fail.
- **NDI source list latency**: Discovered NDI sources are refreshed each polling cycle. New sources may take up to one scan interval to appear.
- **CPU Usage and Core Temperature** are disabled by default since they are primarily diagnostic; enable them in the entity settings if needed.

## Use cases

- **Broadcast monitoring**: Display the active NDI source, connection status, and device health on a Home Assistant dashboard for at-a-glance production monitoring.
- **Automated source switching**: Use automations to switch NDI inputs based on schedules, triggers from other integrations, or manual dashboard controls.
- **Health alerting**: Send notifications when the device status changes to `error`, the NDI connection drops, or CPU/temperature exceed thresholds.
- **Multi-device management**: Add multiple Magewell Pro Convert devices to monitor and control an entire NDI decoder fleet from a single dashboard.

## Automation examples

**Notify when NDI connection drops:**
```yaml
automation:
  - alias: "Magewell NDI disconnected alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.magewell_ndi_connected
        to: "off"
    action:
      - service: notify.notify
        data:
          title: "Magewell Alert"
          message: "NDI source disconnected on {{ trigger.to_state.attributes.friendly_name }}"
```

**Switch NDI source on schedule:**
```yaml
automation:
  - alias: "Switch to Camera 2 at noon"
    trigger:
      - platform: time
        at: "12:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.magewell_ndi_source_select
        data:
          option: "Camera 2"
```

## Troubleshooting

- **Cannot connect during setup**: Verify the device IP is correct and reachable. Try accessing `http://<host>/mwapi?method=login&id=Admin&pass=<md5hash>` in a browser.
- **Invalid auth**: Confirm the username and password match the device's web UI credentials. The default username is `Admin`.
- **Entities show unavailable**: The device may have rebooted or lost network connectivity. Check the device's web UI. If the issue persists, the integration will create a repair issue after 5 consecutive failures.
- **NDI source list is empty**: The decoder may not see any NDI sources on the network. Verify NDI traffic can reach the device (multicast/unicast routing).
- **Stale data after changing settings on the device web UI**: Changes made outside Home Assistant are picked up on the next poll cycle. Reduce the scan interval or manually trigger a refresh.

## Removal

1. Go to **Settings > Devices & Services**
2. Find the **Magewell Pro Convert** integration and click on it
3. Click the three-dot menu on the device entry and select **Delete**
4. If installed via HACS, open HACS > **Integrations**, find **Magewell Pro Convert**, and click **Remove**
5. If installed manually, delete the `custom_components/magewell/` directory
6. Restart Home Assistant

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
