# Claude STWIN.box Diagnostics

### Open-source AI agents for industrial vibration diagnostics with STEVAL-STWINBX1 + Claude + MCP

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://github.com/LGDiMaggio/claude-stwinbox-diagnostics/releases"><img src="https://img.shields.io/github/v/release/LGDiMaggio/claude-stwinbox-diagnostics?display_name=release" alt="Latest release"></a>
  <a href="https://doi.org/10.5281/zenodo.18808856"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.18808856.svg" alt="DOI"></a>
  <a href="https://github.com/LGDiMaggio/claude-stwinbox-diagnostics/actions"><img src="https://img.shields.io/badge/CI-TODO%3A%20replace%20with%20actual%20CI%20badge-lightgrey" alt="CI status placeholder"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-1.0-green.svg" alt="MCP Protocol"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://www.st.com/en/evaluation-tools/steval-stwinbx1.html"><img src="https://img.shields.io/badge/ST-STEVAL--STWINBX1-03234B.svg" alt="STEVAL-STWINBX1"></a>
</p>

> **Il primo agente AI open-source che porta la diagnostica vibrazionale esperta direttamente nella conversazione. Dall''hardware edge all''analisi basata su standard in linguaggio naturale.**
>
> This repository provides a practical reference architecture to connect industrial vibration sensing (STEVAL-STWINBX1) with Claude through MCP, using transparent DSP and standards-based checks (FFT, envelope analysis, ISO 10816/20816-oriented severity guidance).

<p align="center">
  <img src="docs/images/Gif_Edge.gif" alt="Short demo of edge diagnostic workflow" width="800">
</p>

<p align="center">
  <img src="docs/images/claude-stwinbox-diagnostics.png" alt="Claude STWIN.box Diagnostics — System Overview" width="800">
</p>

## Project status (read first)

> **⚠️ PoC / experimental stage.** This project is early-stage and intended as a transparent technical proof-of-concept. Algorithms are based on established vibration-analysis methods, but full industrial validation and long-term field qualification are still in progress. Do **not** use outputs as the sole basis for safety-critical maintenance decisions without independent engineering verification.

> **Independence disclaimer.** This is an independent open-source project and is not affiliated with, endorsed by, or sponsored by Anthropic or STMicroelectronics. Product names are used only for interoperability/context.

## Why this exists

Industrial predictive maintenance often requires fragmented tools and specialist workflows. This project demonstrates a reproducible way to:

- acquire vibration data from STWIN.box sensors,
- analyze signals through explicit DSP/fault heuristics,
- expose those capabilities via MCP tools, and
- orchestrate them through Claude Skills in natural language.

## Quick start (minimum realistic steps)

```bash
# 1) Clone repository
git clone https://github.com/LGDiMaggio/claude-stwinbox-diagnostics.git && cd claude-stwinbox-diagnostics

# 2) Install both MCP servers (editable)
uv pip install -e mcp-servers/stwinbox-sensor-mcp -e mcp-servers/vibration-analysis-mcp

# 3) Read config + run instructions
open docs/getting-started.md  # on Linux use: xdg-open docs/getting-started.md
```

Then configure your MCP client (Claude Desktop / Claude.ai compatible runtime) as documented in [docs/getting-started.md](docs/getting-started.md).

## Navigation

- 📄 Paper / DOI: [10.5281/zenodo.18808856](https://doi.org/10.5281/zenodo.18808856)
- 📚 Documentation index: [docs/](docs/) and [docs/getting-started.md](docs/getting-started.md)
- 🧪 Examples: [examples/README.md](examples/README.md)
- 🤝 Contributing guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- 🔐 Security policy: [SECURITY.md](SECURITY.md)
- 🏷️ Releases: [GitHub Releases](https://github.com/LGDiMaggio/claude-stwinbox-diagnostics/releases)
- 🗺️ Roadmap: [docs/roadmap.md](docs/roadmap.md)
- 🎬 Demo assets plan: [docs/demo-assets.md](docs/demo-assets.md)

## Who this is for

- **Developers** building MCP-enabled industrial AI workflows and tool integrations.
- **Researchers** exploring LLM-assisted diagnostics and human-in-the-loop condition monitoring.
- **OEMs / system integrators** evaluating conversational maintenance interfaces on edge sensor stacks.

## Components

### MCP servers

| Server | Purpose | Key tools |
|---|---|---|
| [stwinbox-sensor-mcp](mcp-servers/stwinbox-sensor-mcp/) | Hardware communication with STWIN.box via USB-HID (DATALOG2) or USB-Serial | `datalog2_connect`, `datalog2_start_acquisition`, `datalog2_stop_acquisition`, `datalog2_list_sensors`, `datalog2_configure_sensor`, `connect_board`, `acquire_data`, `load_data_from_file` |
| [vibration-analysis-mcp](mcp-servers/vibration-analysis-mcp/) | Signal processing, data loading, and fault detection | `load_signal`, `list_stored_signals`, `compute_fft_spectrum`, `compute_envelope_spectrum`, `check_bearing_fault_peak`, `check_bearing_faults_direct`, `diagnose_vibration`, `assess_vibration_severity` |

### Claude skills

| Skill | Purpose |
|---|---|
| [machine-vibration-monitoring](skills/machine-vibration-monitoring/) | Sensor acquisition + baseline/threshold workflow |
| [vibration-fault-diagnosis](skills/vibration-fault-diagnosis/) | Multi-step fault diagnosis workflow |
| [operator-diagnostic-report](skills/operator-diagnostic-report/) | Human-readable maintenance report generation |

## Supported diagnostics scope

| Fault | Detection method | Indicators |
|---|---|---|
| Bearing inner race (BPFI) | Envelope analysis | Harmonics of BPFI |
| Bearing outer race (BPFO) | Envelope analysis | Harmonics of BPFO |
| Bearing rolling element (BSF) | Envelope analysis | Harmonics of BSF |
| Bearing cage (FTF) | Envelope analysis | Harmonics of FTF |
| Unbalance | FFT | 1× RPM dominant |
| Misalignment | FFT | 1× and 2× RPM |
| Mechanical looseness | FFT | Multiple RPM harmonics |

## STWIN.box sensors currently used

| Sensor | Type | Typical use |
|---|---|---|
| IIS3DWB | 3-axis vibration | Wideband vibration monitoring |
| ISM330DHCX | 6-axis IMU | Medium-frequency vibration |
| IMP23ABSU | Analog microphone | Acoustic/ultrasound indicators |
| STTS22H | Temperature | Thermal context |
| ILPS22QS | Pressure | Environmental context |

## Architecture

- Claude (host runtime) invokes MCP tools exposed by two servers.
- Skills orchestrate workflows for monitoring, diagnosis, and reporting.
- Sensor data can come from USB acquisition or file-based workflows.
- Analysis server executes DSP/fault checks and returns interpretable metrics.

See [docs/architecture.md](docs/architecture.md) for the complete architecture view, detailed sensor specs, and project structure.

## Call to action

- ⭐ **Star the repository** if this project is useful to your work.
- 🐛 **Open an issue** for bugs or reproducible diagnostic mismatches.
- 💬 **Open a discussion** for usage questions, ideas, and datasets.
- 🤝 **Contribute** via [CONTRIBUTING.md](CONTRIBUTING.md).
- 📚 **Cite the work** using [CITATION.cff](CITATION.cff) and the DOI.


## Recommended GitHub community configuration

If you maintain the repository settings, enable GitHub Discussions with these categories:

- **Q&A**
- **Ideas**
- **Show and tell / use cases**
- **Research & datasets**
- **Announcements**

Recommended repository topics:

`predictive-maintenance`, `vibration-analysis`, `industrial-ai`, `mcp`, `claude-ai`, `iot`, `edge-ai`, `condition-monitoring`, `fault-diagnosis`, `industry-4-0`, `stm32`, `stwinbox`

## Citation

If you use this project in research or technical reports, cite:

```bibtex
@software{llm_edge_diagnostics,
  author       = {Di Maggio, Luigi Gianpio},
  title        = {LLM Edge Predictive Maintenance: Bridging Industrial IoT Sensors and Large Language Models for Predictive Maintenance},
  year         = {2026},
  url          = {https://github.com/LGDiMaggio/claude-stwinbox-diagnostics},
  doi          = {10.5281/zenodo.18808856},
  license      = {Apache-2.0}
}
```

## Governance & references

- Consistency checklist: [docs/consistency-governance.md](docs/consistency-governance.md)
- Hardware and standards references are listed in [docs/getting-started.md](docs/getting-started.md) and server READMEs.
- Third-party license attribution: [NOTICE](NOTICE)

## License

Licensed under Apache License 2.0. See [LICENSE](LICENSE).