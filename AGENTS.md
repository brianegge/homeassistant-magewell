# AGENTS.md -- Development Guide for AI Agents

This is a Home Assistant custom integration for Magewell Pro Convert NDI decoders.

## Project structure

```
custom_components/magewell/
├── __init__.py        # Entry setup/teardown, creates client + coordinator
├── api.py             # MagewellClient -- async HTTP client for the device API
├── config_flow.py     # UI-based configuration flow (single step)
├── coordinator.py     # DataUpdateCoordinator -- polls device on interval
├── const.py           # Constants (domain, defaults, platform list)
├── sensor.py          # 4 sensors + MagewellEntity base class
├── binary_sensor.py   # NDI Connected binary sensor
├── select.py          # NDI Source Select entity
├── manifest.json      # HA integration metadata
└── strings.json       # Translatable UI strings
```

## Architecture

### Data flow

1. `__init__.py` creates a `MagewellClient` and `MagewellCoordinator` per config entry
2. The coordinator polls the device at the configured interval (default 30s) calling three API methods: `get-summary-info`, `get-channel`, `get-ndi-sources`
3. All entity platforms (`sensor`, `binary_sensor`, `select`) read from `coordinator.data`
4. The select entity writes back to the device via `client.set_channel()`

### Key classes

- **`MagewellClient`** (`api.py`) -- async HTTP client using `aiohttp`. Handles login with MD5 password hashing, session management with automatic re-login on expiry, and persistent TCP connections with keepalive.
- **`MagewellCoordinator`** (`coordinator.py`) -- standard HA `DataUpdateCoordinator`. Returns a dict with keys: `summary`, `channel`, `ndi_sources`.
- **`MagewellEntity`** (`sensor.py`) -- base `CoordinatorEntity` subclass providing shared `device_info` for all entities. All entity classes inherit from this.

### Device API

The device exposes an HTTP API at `http://<host>/mwapi` using GET requests with query parameters. Key methods:

| API method | Purpose |
|------------|---------|
| `login` | Authenticate (params: `id`, `pass` as MD5 hash) |
| `get-summary-info` | Device status, NDI state, CPU, temperature |
| `get-channel` | Current active NDI source |
| `get-ndi-sources` | All discovered NDI sources on the network |
| `set-channel` | Switch NDI input (param: `ndi-name`) |
| `list-channels` | Saved preset channels |

Authentication uses cookie-based sessions. The client automatically re-logs in when a request returns a non-zero status.

### Error handling

- `MagewellApiError` -- base exception for connection/API errors
- `MagewellAuthError` -- authentication failures (subclass of above)
- The coordinator wraps API errors in `UpdateFailed` for HA's retry logic

## Conventions

- Follows standard Home Assistant custom component patterns
- Uses `has_entity_name = True` -- entity names are relative to the device name
- Diagnostic entities (CPU, temperature) use `EntityCategory.DIAGNOSTIC`
- Unique IDs follow the pattern `{entry_id}_{entity_key}`
- No external Python dependencies beyond what HA provides (`aiohttp`)
- Config flow uses the device host IP as the unique ID for duplicate prevention

## Common tasks

### Adding a new sensor

1. Create a new class in `sensor.py` (or `binary_sensor.py`) inheriting from `MagewellEntity` and the appropriate HA entity class
2. Set `_attr_unique_id`, `_attr_name`, and any device class / unit attributes
3. Implement `native_value` (or `is_on` for binary sensors) reading from `self.coordinator.data`
4. Register it in the `async_setup_entry` function of the same file

### Adding a new API method

1. Add the method to `MagewellClient` in `api.py` using `self._call("method-name")`
2. If it's needed on every poll, add the call to `MagewellCoordinator._async_update_data()` and store the result in the returned dict
3. Access it from entities via `self.coordinator.data["your_key"]`

### Adding a new entity platform

1. Create a new file (e.g., `button.py`, `switch.py`)
2. Add the platform name to the `PLATFORMS` list in `const.py`
3. Implement `async_setup_entry` following the pattern in existing platform files

## Testing

There are currently no automated tests. To test manually:

1. Copy `custom_components/magewell/` into a Home Assistant dev environment
2. Add the integration via the UI with a real Magewell device on the network
3. Verify entities appear and update correctly in Developer Tools > States
