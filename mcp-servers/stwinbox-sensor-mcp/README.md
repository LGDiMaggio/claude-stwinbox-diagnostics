# stwinbox-sensor-mcp

MCP Server for communicating with the **STEVAL-STWINBX1** SensorTile Wireless Industrial Node.

## Features

- Connect/disconnect to STWIN.box via USB serial
- Configure onboard sensors (IIS3DWB, ISM330DHCX, IMP23ABSU, etc.)
- Acquire vibration, temperature, pressure data
- Stream sensor data with configurable duration
- Query board info and sensor status

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
| `load_data_from_file` | Load vibration data from CSV/JSON/NumPy file |

## Hardware Requirements

- STEVAL-STWINBX1 with FP-SNS-DATALOG2 or FP-AI-MONITOR2 firmware
- USB-C cable
- (Optional) microSD card for offline logging
