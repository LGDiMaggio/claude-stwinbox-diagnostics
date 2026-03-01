# Claude STWIN.box Diagnostics

### AI-Powered Predictive Maintenance & Vibration Fault Diagnosis — Bridging Edge Sensors and Large Language Models

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://doi.org/10.5281/zenodo.18808856"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.18808856.svg" alt="DOI"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-1.0-green.svg" alt="MCP Protocol"></a>
  <a href="https://docs.anthropic.com"><img src="https://img.shields.io/badge/Claude-Skills-orange.svg" alt="Claude Skills"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://www.st.com/en/evaluation-tools/steval-stwinbx1.html"><img src="https://img.shields.io/badge/ST-STWIN.box-03234B.svg" alt="STWIN.box"></a>
  <a href="https://lgdimaggio.github.io/claude-stwinbox-diagnostics/"><img src="https://img.shields.io/badge/🌐_Landing_Page-Visit-blueviolet.svg" alt="Landing Page"></a>
</p>

<p align="center">
  <strong>An open-source reference architecture for connecting industrial MEMS sensors to LLM-based diagnostic assistants using the Model Context Protocol (MCP).</strong>
</p>

---

> **Why this project?** Industrial predictive maintenance has traditionally required specialized software and deep domain expertise. By combining low-cost edge sensor hardware (STEVAL-STWINBX1) with the reasoning capabilities of large language models (Claude) through a standardised protocol (MCP), we make machine diagnostics **conversational, accessible, and extensible**. Ask your machine how it's feeling — in natural language.

## Key Features

- **Plug & Analyze** — Connect the STWIN.box via USB, ask Claude to check your machine
- **Full DSP Pipeline** — FFT, PSD, spectrogram (STFT), envelope analysis (Hilbert transform)
- **Bearing Fault Detection** — BPFO / BPFI / BSF / FTF with built-in bearing database, custom geometry, or direct frequency input from manufacturer catalogs (SKF, Schaeffler, NSK, NTN)
- **Automated Classification** — Unbalance, misalignment, looseness, bearing defects
- **ISO 10816 Severity** — Standards-based vibration severity assessment
- **Operator-Friendly Reports** — Generates clear maintenance reports for non-experts
- **Extensible Architecture** — Add sensors, fault types, or analysis methods easily

<p align="center">
  <img src="docs/images/claude-stwinbox-diagnostics.png" alt="Claude STWIN.box Diagnostics — System Overview" width="800">
</p>

## Use Cases

| Scenario | Skills & Servers Used |
|----------|----------------------|
| "Check vibration on my pump" | monitoring skill → sensor MCP → analysis MCP |
| "Is this bearing degrading?" | diagnosis skill → analysis MCP (envelope) |
| "Generate a report for maintenance" | report skill → analysis MCP |
| "Compare to last month's baseline" | monitoring skill → threshold scripts |
| "What bearing fits my 6205 at 1470 RPM?" | analysis MCP (bearing lookup) |

## Overview

This project connects the **STEVAL-STWINBX1** (SensorTile Wireless Industrial Node) to **Claude** for real-time machine condition monitoring and predictive maintenance diagnostics. It provides:

- **2 MCP Servers** for hardware communication and signal analysis
- **3 Claude Skills** for intelligent diagnostics workflow

The system reads vibration data from the STWIN.box MEMS sensors (IIS3DWB, ISM330DHCX), performs frequency-domain analysis (FFT, PSD, envelope analysis), detects common rotating machinery faults (bearing defects, unbalance, misalignment, mechanical looseness), and enables conversational diagnostics with the operator.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude (LLM Host)                      │
│                                                             │
│  ┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │  machine-       │ │  vibration-  │ │  operator-       │ │
│  │  vibration-     │ │  fault-      │ │  diagnostic-     │ │
│  │  monitoring     │ │  diagnosis   │ │  report          │ │
│  │  (Skill)        │ │  (Skill)     │ │  (Skill)         │ │
│  └────────┬────────┘ └──────┬───────┘ └────────┬─────────┘ │
│           │                 │                   │           │
│  ┌────────▼─────────────────▼───────────────────▼─────────┐ │
│  │              MCP Client (Claude Runtime)                │ │
│  └────────┬─────────────────────────────────┬─────────────┘ │
└───────────┼─────────────────────────────────┼───────────────┘
            │                                 │
   ┌────────▼────────┐              ┌────────▼────────┐
   │  stwinbox-      │              │  vibration-     │
   │  sensor-mcp     │              │  analysis-mcp   │
   │  (MCP Server)   │              │  (MCP Server)   │
   │                 │              │                 │
   │  • USB/Serial   │              │  • FFT          │
   │  • Sensor cfg   │              │  • Envelope     │
   │  • Data acquire │              │  • ISO 10816   │
   │  • Stream ctrl  │              │  • Fault detect │
   │  • DATALOG2 ctl │              │                 │
   └────────┬────────┘              └─────────────────┘
            │
   ┌────────▼────────┐
   │  STEVAL-        │
   │  STWINBX1       │
   │  (USB-HID/PnPL) │
   │                 │
   │  IIS3DWB (vib)  │
   │  ISM330DHCX     │
   │  IMP23ABSU(mic) │
   │  STTS22H (temp) │
   │  ILPS22QS(pres) │
   └─────────────────┘
```

## Components

### MCP Servers

| Server | Purpose | Key Tools |
|--------|---------|-----------|
| [stwinbox-sensor-mcp](mcp-servers/stwinbox-sensor-mcp/) | Hardware communication with STWIN.box via USB-HID (DATALOG2) or USB-Serial | `datalog2_connect`, `datalog2_start_acquisition(duration_s)`, `datalog2_stop_acquisition`, `datalog2_list_sensors`, `datalog2_configure_sensor`, `connect_board`, `acquire_data` |
| [vibration-analysis-mcp](mcp-servers/vibration-analysis-mcp/) | Signal processing, data loading, and fault detection | `load_signal`, `compute_fft_spectrum`, `compute_envelope_spectrum`, `check_bearing_fault_peak`, `diagnose_vibration`, `assess_vibration_severity` |

### Claude Skills

| Skill | Category | Purpose |
|-------|----------|---------|
| [machine-vibration-monitoring](skills/machine-vibration-monitoring/) | MCP Enhancement | Orchestrates sensor acquisition + baseline comparison |
| [vibration-fault-diagnosis](skills/vibration-fault-diagnosis/) | Workflow Automation | Multi-step fault diagnosis with frequency analysis |
| [operator-diagnostic-report](skills/operator-diagnostic-report/) | Document & Asset Creation | Generates human-readable diagnostic reports |

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://astral.sh/uv) (recommended) or pip
- STEVAL-STWINBX1 board with FP-SNS-DATALOG2 firmware
- USB-C cable
- Claude Desktop or Claude.ai with MCP support

### 1. Install MCP Servers

```bash
# Clone the repo
git clone https://github.com/LGDiMaggio/claude-stwinbox-diagnostics.git
cd claude-stwinbox-diagnostics

# Install stwinbox-sensor-mcp
cd mcp-servers/stwinbox-sensor-mcp
uv venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .
cd ../..

# Install vibration-analysis-mcp
cd mcp-servers/vibration-analysis-mcp
uv venv && source .venv/bin/activate
uv pip install -e .
cd ../..
```

### 2. (Optional) Install FP-SNS-DATALOG2 SDK

For programmatic acquisition control (start/stop logging via USB, no need to
press buttons or extract the SD card) and native DATALOG2 `.dat` file loading,
install the STDATALOG-PYSDK **into both server virtual environments**:

```bash
# Clone the SDK (packages are not on PyPI)
git clone --recursive https://github.com/STMicroelectronics/stdatalog-pysdk.git

# Install into the sensor server venv (enables datalog2_* tools)
cd mcp-servers/stwinbox-sensor-mcp
uv pip install ../../stdatalog-pysdk/stdatalog_pnpl/
uv pip install ../../stdatalog-pysdk/stdatalog_core/
cd ../..

# Install into the analysis server venv (enables DATALOG2 folder loading in load_signal)
cd mcp-servers/vibration-analysis-mcp
uv pip install ../../stdatalog-pysdk/stdatalog_pnpl/
uv pip install ../../stdatalog-pysdk/stdatalog_core/
cd ../..
```

This enables the `datalog2_*` tools in the sensor server and native DATALOG2
folder loading via `load_signal` in the analysis server. Without the SDK
installed, those features gracefully report that the SDK is unavailable while
all other tools continue to work normally.

> **Note:** When the SDK is installed, both servers must be launched using the
> venv's Python directly (not `uv run`, which would re-sync and remove the
> SDK). See the config example below.

### 3. Configure Claude Desktop

Add to your `claude_desktop_config.json`:

**Without SDK** (SD card workflow only):
```json
{
  "mcpServers": {
    "stwinbox-sensor": {
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/TO/mcp-servers/stwinbox-sensor-mcp", "run", "stwinbox_sensor_mcp"]
    },
    "vibration-analysis": {
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/TO/mcp-servers/vibration-analysis-mcp", "run", "vibration_analysis_mcp"]
    }
  }
}
```

**With SDK installed** (USB-HID live acquisition + DATALOG2 folder loading):
```json
{
  "mcpServers": {
    "stwinbox-sensor": {
      "command": "/ABSOLUTE/PATH/TO/mcp-servers/stwinbox-sensor-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "stwinbox_sensor_mcp"]
    },
    "vibration-analysis": {
      "command": "/ABSOLUTE/PATH/TO/mcp-servers/vibration-analysis-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "vibration_analysis_mcp"]
    }
  }
}
```

### 4. Install Skills

**Claude.ai:**
1. Zip each skill folder (e.g., `skills/machine-vibration-monitoring/`)
2. Go to Settings > Capabilities > Skills
3. Upload each .zip

**Claude Code:**
Place skill folders in your Claude Code skills directory.

### 5. Test

```
You: "Connect to my STWIN.box and check vibration levels on the IIS3DWB sensor"
Claude: [Uses machine-vibration-monitoring skill + stwinbox-sensor-mcp]

You: "Analyze the vibration data for bearing faults"
Claude: [Uses vibration-fault-diagnosis skill + vibration-analysis-mcp]

You: "Generate a diagnostic report for the maintenance team"
Claude: [Uses operator-diagnostic-report skill]
```

## Supported Fault Types

| Fault | Detection Method | Frequency Indicators |
|-------|-----------------|---------------------|
| **Bearing Inner Race (BPFI)** | Envelope analysis | N × BPFI harmonics |
| **Bearing Outer Race (BPFO)** | Envelope analysis | N × BPFO harmonics |
| **Bearing Ball/Roller (BSF)** | Envelope analysis | N × BSF harmonics |
| **Unbalance** | FFT | 1× RPM dominant |
| **Misalignment** | FFT | 1×, 2× RPM |
| **Mechanical Looseness** | FFT | Multiple harmonics of RPM |

## STWIN.box Sensors Used

| Sensor | Type | Key Specs | Use Case |
|--------|------|-----------|----------|
| **IIS3DWB** | 3-axis vibration | 26.7 kHz ODR, ±16g | Wideband vibration monitoring |
| **ISM330DHCX** | 6-axis IMU | Up to 6.7 kHz, ML Core | Medium-frequency vibration |
| **IMP23ABSU** | Analog microphone | Up to 80 kHz | Ultrasound / acoustic emission |
| **STTS22H** | Temperature | ±0.5°C accuracy | Thermal monitoring |
| **ILPS22QS** | Pressure | 1.26 / 4 bar | Environmental conditions |

## Project Structure

```
claude-stwinbox-diagnostics/
├── README.md
├── LICENSE
├── mcp-servers/
│   ├── stwinbox-sensor-mcp/          # MCP Server: HW communication
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   └── stwinbox_sensor_mcp/
│   │   │       ├── __init__.py
│   │   │       ├── __main__.py
│   │   │       ├── server.py          # FastMCP server definition
│   │   │       ├── serial_comm.py     # USB/Serial communication
│   │   │       ├── datalog2_comm.py   # DATALOG2 USB-HID/PnPL communication
│   │   │       └── sensor_config.py   # Sensor configuration helpers
│   │   └── tests/
│   └── vibration-analysis-mcp/        # MCP Server: DSP & fault detection
│       ├── pyproject.toml
│       ├── src/
│       │   └── vibration_analysis_mcp/
│       │       ├── __init__.py
│       │       ├── __main__.py
│       │       ├── server.py          # FastMCP server definition
│       │       ├── data_store.py      # Signal storage + DATALOG2 folder loading
│       │       ├── fft_analysis.py    # FFT, PSD, spectrogram
│       │       ├── envelope.py        # Envelope analysis for bearings
│       │       ├── fault_detection.py # Fault classification logic
│       │       └── bearing_freqs.py   # BPFI/BPFO/BSF/FTF calculators
│       └── tests/
├── skills/
│   ├── machine-vibration-monitoring/  # Skill 1: Monitoring workflow
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   └── sensor-specs.md
│   │   └── scripts/
│   │       └── check_thresholds.py
│   ├── vibration-fault-diagnosis/     # Skill 2: Diagnosis workflow
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── fault-signatures.md
│   │   │   └── iso-10816-guide.md
│   │   └── scripts/
│   │       └── classify_fault.py
│   └── operator-diagnostic-report/    # Skill 3: Report generation
│       ├── SKILL.md
│       ├── references/
│       │   └── report-guidelines.md
│       └── assets/
│           └── report-template.md
├── docs/
│   └── images/
├── examples/
│   ├── README.md
│   ├── generate_sample_data.py
│   └── sample_data/
└── .gitignore
```

## Project Status & Disclaimer

> **⚠️ Early-stage project.** This release (v0.2.0) was developed as a proof-of-concept with intensive assistance from Claude and has **not yet been validated extensively on real industrial machinery**. The analysis algorithms implement well-established signal processing techniques (FFT, envelope analysis, ISO 10816), but their integration with the STWIN.box hardware and the MCP protocol should be considered experimental. Real-world testing, calibration, and refinement will follow in subsequent versions. **Do not use this as the sole basis for critical maintenance decisions without independent verification.**

## Contributing

Contributions are welcome! Whether it's new bearing data, additional fault signatures, sensor integrations, or documentation improvements.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add feature'`)
4. Push (`git push origin feature/my-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Roadmap

- [ ] Real-time streaming mode (WebSocket transport)
- [x] Support for FP-SNS-DATALOG2 `.dat` file format via STDATALOG-PYSDK
- [ ] Additional fault types: electrical faults (rotor bar, stator), gear mesh
- [ ] Trend storage and historical comparison database
- [ ] Integration with Grafana/InfluxDB for dashboards
- [ ] Docker container for analysis MCP server
- [ ] Support for additional boards (SensorTile.box PRO, STWIN.box PRO)
- [ ] Multi-language report generation (IT, EN, DE, FR)

## References & Further Reading

### Hardware & Firmware
- [STEVAL-STWINBX1 Product Page](https://www.st.com/en/evaluation-tools/steval-stwinbx1.html)
- [FP-AI-MONITOR2 User Manual](https://wiki.st.com/stm32mcu/wiki/AI:FP-AI-MONITOR2_user_manual)
- [FP-SNS-DATALOG2 GitHub](https://github.com/STMicroelectronics/fp-sns-datalog2)
- [STDATALOG-PYSDK](https://github.com/STMicroelectronics/stdatalog-pysdk)

### AI & Protocol
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io) — Open standard for LLM-tool integration
- [Claude Skills Guide](https://docs.anthropic.com) — How to build Claude skills
- [Anthropic API Documentation](https://docs.anthropic.com/en/docs)

### Vibration Analysis Standards
- [ISO 10816 - Vibration Severity](https://www.iso.org/standard/18866.html)
- [ISO 20816 - Mechanical Vibration](https://www.iso.org/standard/63180.html) (successor to ISO 10816)

## Citation

If you use this project in academic work or industrial applications, please cite:

```bibtex
@software{claude_edge_diagnostics,
  author       = {Di Maggio, Luigi Gianpio},
  title        = {Claude Edge Predictive Maintenance: Bridging
                  Industrial IoT Sensors and Large Language Models
                  for Predictive Maintenance},
  year         = {2026},
  url          = {https://github.com/LGDiMaggio/claude-stwinbox-diagnostics},
  doi          = {10.5281/zenodo.18808856},
  license      = {Apache-2.0}
}
```

A [CITATION.cff](CITATION.cff) file is included for automatic citation via GitHub and Zenodo.

## License

Licensed under the Apache License, Version 2.0 — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with ❤️ for condition monitoring professionals — Connecting the physical world to AI, one vibration at a time.</sub>
</p>
