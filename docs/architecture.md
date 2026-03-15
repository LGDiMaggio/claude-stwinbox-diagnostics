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
   - Preferentially calls `datalog2_connect` → `datalog2_start_acquisition(duration_s=...)` on **stwinbox-sensor-mcp**
   - Loads the generated acquisition folder with `load_signal` on **vibration-analysis-mcp**
   - Falls back to `connect_board`/`acquire_data` only when DATALOG2 SDK is unavailable
3. Claude then calls `compute_fft_spectrum` (and optionally `find_spectral_peaks`) on **vibration-analysis-mcp**
4. Results are presented with explicit units, evidence references, and severity assessment

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
        "run", "stwinbox_sensor_mcp"
      ]
    },
    "vibration-analysis": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/mcp-servers/vibration-analysis-mcp",
        "run", "vibration_analysis_mcp"
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

## Sensor specifications

| Sensor | Type | Key specs | Typical use case |
|--------|------|-----------|------------------|
| **IIS3DWB** | 3-axis vibration | 26.7 kHz ODR, ±16g | Wideband vibration monitoring |
| **ISM330DHCX** | 6-axis IMU | Up to 6.7 kHz, ML Core | Medium-frequency vibration |
| **IMP23ABSU** | Analog microphone | Up to 80 kHz | Ultrasound / acoustic emission |
| **STTS22H** | Temperature | ±0.5°C accuracy | Thermal monitoring |
| **ILPS22QS** | Pressure | 1.26 / 4 bar | Environmental conditions |

## Supported fault types (reference)

| Fault | Detection method | Frequency indicators |
|-------|-----------------|---------------------|
| **Bearing inner race (BPFI)** | Envelope analysis | N × BPFI harmonics |
| **Bearing outer race (BPFO)** | Envelope analysis | N × BPFO harmonics |
| **Bearing ball/roller (BSF)** | Envelope analysis | N × BSF harmonics |
| **Bearing cage (FTF)** | Envelope analysis | N × FTF harmonics |
| **Unbalance** | FFT | 1× RPM dominant |
| **Misalignment** | FFT | 1×, 2× RPM |
| **Mechanical looseness** | FFT | Multiple harmonics of RPM |

## Project structure

```
claude-stwinbox-diagnostics/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── CONTRIBUTING.md
├── CITATION.cff
├── NOTICE
├── mcp-servers/
│   ├── stwinbox-sensor-mcp/          # MCP Server: HW communication
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   └── stwinbox_sensor_mcp/
│   │   │       ├── server.py          # FastMCP server definition
│   │   │       ├── serial_comm.py     # USB/Serial communication
│   │   │       ├── datalog2_comm.py   # DATALOG2 USB-HID/PnPL communication
│   │   │       └── sensor_config.py   # Sensor configuration helpers
│   │   └── tests/
│   └── vibration-analysis-mcp/        # MCP Server: DSP & fault detection
│       ├── pyproject.toml
│       ├── src/
│       │   └── vibration_analysis_mcp/
│       │       ├── server.py          # FastMCP server definition
│       │       ├── data_store.py      # Signal storage + DATALOG2 folder loading
│       │       ├── fft_analysis.py    # FFT, PSD, spectrogram
│       │       ├── envelope.py        # Envelope analysis for bearings
│       │       ├── fault_detection.py # Fault classification logic
│       │       └── bearing_freqs.py   # BPFI/BPFO/BSF/FTF calculators
│       └── tests/
├── skills/
│   ├── machine-vibration-monitoring/  # Skill 1: Monitoring workflow
│   ├── vibration-fault-diagnosis/     # Skill 2: Diagnosis workflow
│   └── operator-diagnostic-report/    # Skill 3: Report generation
├── docs/
│   ├── architecture.md
│   ├── getting-started.md
│   ├── consistency-governance.md
│   ├── roadmap.md
│   ├── demo-assets.md
│   └── images/
├── examples/
│   ├── README.md
│   ├── generate_sample_data.py
│   └── sample_data/
└── scripts/
    └── build_skill_zips.py
```

## Third-party components

| Component | Copyright | License |
|-----------|-----------|---------|
| [STDATALOG-PYSDK](https://github.com/STMicroelectronics/stdatalog-pysdk) (`stdatalog_core`, `stdatalog_pnpl`) | © 2022 STMicroelectronics | BSD-3-Clause |
| [FP-SNS-DATALOG2](https://github.com/STMicroelectronics/fp-sns-datalog2) firmware protocol | © STMicroelectronics | Mixed (see repo) |

The vendored `stdatalog-pysdk/` directory contains the full STDATALOG-PYSDK source under its original BSD-3-Clause license. See the [NOTICE](../NOTICE) file for full attribution.
