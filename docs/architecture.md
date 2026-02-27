# Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────┐
│                     Claude Desktop                       │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Skills (SKILL.md)│  │ User conversation│              │
│  │ • monitoring     │  │ "Check my pump" │              │
│  │ • diagnosis      │  │                 │              │
│  │ • reporting      │  └────────┬────────┘              │
│  └────────┬────────┘           │                        │
│           │    ┌───────────────┘                        │
│           ▼    ▼                                        │
│  ┌─────────────────────────────────────────┐           │
│  │           MCP Client (Claude)            │           │
│  │  • Discovers tools from MCP servers      │           │
│  │  • Orchestrates multi-step workflows     │           │
│  │  • Interprets results for the user       │           │
│  └──────┬───────────────────┬──────────────┘           │
│         │ STDIO             │ STDIO                     │
└─────────┼───────────────────┼───────────────────────────┘
          │                   │
          ▼                   ▼
┌─────────────────┐  ┌─────────────────────┐
│ stwinbox-sensor  │  │ vibration-analysis   │
│ MCP Server       │  │ MCP Server           │
│                  │  │                      │
│ • Serial comm    │  │ • FFT / PSD          │
│ • Sensor config  │  │ • Envelope analysis  │
│ • Data acquire   │  │ • Bearing frequencies│
│ • File I/O       │  │ • Fault detection    │
│                  │  │ • ISO 10816          │
└────────┬─────────┘  └──────────────────────┘
         │
         │ USB Serial
         ▼
┌─────────────────┐
│  STEVAL-STWINBX1 │
│  (STWIN.box)     │
│                  │
│  IIS3DWB         │ ← Wideband vibration (26.7 kHz)
│  ISM330DHCX      │ ← 6-axis IMU + ML Core
│  IMP23ABSU       │ ← Ultrasonic microphone
│  STTS22H         │ ← Temperature
│  ILPS22QS        │ ← Pressure
│  IIS2ICLX        │ ← Inclinometer
│  IIS2DLPC        │ ← Low-power accelerometer
│  IIS2MDC         │ ← Magnetometer
└─────────────────┘
```

## Data Flow

### Acquisition Flow
1. User asks Claude to monitor a machine
2. Claude (guided by the **machine-vibration-monitoring** skill):
   - Calls `connect_board` → `apply_preset` → `acquire_data` on **stwinbox-sensor-mcp**
   - Receives raw time-domain acceleration data as JSON arrays
3. Claude then calls `compute_fft_spectrum` on **vibration-analysis-mcp**
4. Results presented to user with severity assessment

### Diagnosis Flow
1. User asks "What's wrong with my motor?"
2. Claude (guided by the **vibration-fault-diagnosis** skill):
   - Acquires data (or uses provided data)
   - Runs `diagnose_vibration` for full automated pipeline, OR:
   - Step-by-step: FFT → peak finding → bearing frequency calc → envelope analysis → fault classification
3. Results cross-referenced with fault signatures from skill references

### Reporting Flow
1. After diagnosis, user asks for a report
2. Claude (guided by the **operator-diagnostic-report** skill):
   - Formats findings using the report template
   - Includes ISO 10816 severity, fault table, recommendations
   - Outputs Markdown report

## MCP Transport

Both servers use **STDIO transport** (standard input/output):
- Claude Desktop spawns each server as a subprocess
- Communication via JSON-RPC 2.0 over stdin/stdout
- No network ports required
- Configured in `claude_desktop_config.json`

## Configuration

### Claude Desktop Config (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "stwinbox-sensor": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/mcp-servers/stwinbox-sensor-mcp",
        "run", "stwinbox-sensor-mcp"
      ]
    },
    "vibration-analysis": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/mcp-servers/vibration-analysis-mcp",
        "run", "vibration-analysis-mcp"
      ]
    }
  }
}
```

## Security Considerations

- Serial port access requires appropriate OS permissions
- MCP servers run locally — no data leaves the machine (except to Claude API)
- Sensor data can contain proprietary machine signatures — handle accordingly
- The `acquire_data` tool has configurable duration limits to prevent excessively long acquisitions
