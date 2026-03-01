# stwinbox-sensor-mcp

MCP Server for communicating with the **STEVAL-STWINBX1** SensorTile Wireless Industrial Node.

## Features

- Connect/disconnect to STWIN.box via USB serial or USB-HID (DATALOG2)
- Configure onboard sensors (IIS3DWB, ISM330DHCX, IMP23ABSU, etc.)
- Acquire vibration, temperature, pressure data
- Programmatic acquisition control with timed mode (`duration_s`)
- Query board info, sensor status, and firmware version
- FP-SNS-DATALOG2 integration via STDATALOG-PYSDK (optional)

## Installation

```bash
uv venv && uv pip install -e .
```

## Usage with Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "stwinbox-sensor": {
      "command": "uv",
      "args": ["--directory", "/path/to/stwinbox-sensor-mcp", "run", "stwinbox_sensor_mcp"]
    }
  }
}
```

## Available Tools

### Serial / General Tools

| Tool | Description |
|------|-------------|
| `list_serial_ports` | List available COM ports |
| `connect_board` | Connect to STWIN.box on a given COM port |
| `disconnect_board` | Disconnect from the board |
| `get_board_info` | Get firmware version, UID, sensor list |
| `list_sensors` | List all onboard sensors with IDs and types |
| `get_sensor_config` | Get current sensor configuration |
| `configure_sensor` | Set ODR, full-scale, enable/disable a sensor |
| `list_sensor_presets` | Show pre-built sensor configurations |
| `apply_preset` | Apply a named preset (e.g., `wideband_vibration`) |
| `recommend_sensor_config` | Get recommended settings for a fault type and RPM |
| `acquire_data` | Acquire N samples from a sensor |
| `load_data_from_file` | Load vibration data from .csv or .dat file |

### FP-SNS-DATALOG2 Tools (require STDATALOG-PYSDK)

| Tool | Description |
|------|-------------|
| `datalog2_status` | Check SDK installation and board connection status |
| `datalog2_connect` | Connect via USB-HID / PnPL protocol |
| `datalog2_disconnect` | Disconnect from the board |
| `datalog2_get_device_info` | Get firmware version, device identity, acquisition status |
| `datalog2_list_sensors` | List PnPL sensor components with ODR/FS/enabled state |
| `datalog2_configure_sensor` | Enable/disable sensors, set ODR and full-scale via PnPL |
| `datalog2_start_acquisition` | Start high-speed logging to SD card (supports `duration_s` for timed mode) |
| `datalog2_stop_acquisition` | Stop logging, save config files, list generated files |
| `datalog2_set_tag` | Set/unset software tags during acquisition |

## Hardware Requirements

- STEVAL-STWINBX1 with FP-SNS-DATALOG2 or FP-AI-MONITOR2 firmware
- USB-C cable
- (Optional) microSD card for offline logging
