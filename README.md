# Condition Monitoring Copilot — LLM Edge Predictive Maintenance

### Open-source condition monitoring copilot and predictive maintenance AI agent — bridging industrial edge sensors and LLMs via MCP and Claude Skills.

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://github.com/LGDiMaggio/claude-stwinbox-diagnostics/releases"><img src="https://img.shields.io/github/v/release/LGDiMaggio/claude-stwinbox-diagnostics?display_name=release" alt="Latest release"></a>
  <a href="https://doi.org/10.5281/zenodo.18808856"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.18808856.svg" alt="DOI"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-1.0-green.svg" alt="MCP Protocol"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://www.st.com/en/evaluation-tools/steval-stwinbx1.html"><img src="https://img.shields.io/badge/ST-STEVAL--STWINBX1-03234B.svg" alt="STEVAL-STWINBX1"></a>
</p>

<p align="center">
  <em><strong>Ask your machine how it's feeling, in natural language.</strong></em>
</p>

> Open-source **condition monitoring copilot** and **predictive maintenance AI agent** that connects industrial MEMS vibration sensors to Claude through MCP. Transparent Digital Signal Processing (DSP) pipeline, standards-based severity checks (ISO 10816/20816), and conversational fault diagnosis out of the box. Acts as a **condition monitoring AI agent** and **AI assistant for predictive maintenance** teams. Currently validated with STWIN.box; the analysis server works with any vibration data source.

<p align="center">
  <img src="docs/images/Gif_Edge.gif" alt="Short demo of edge diagnostic workflow" width="800">
</p>

<p align="center">
  <img src="docs/images/claude-stwinbox-diagnostics.png" alt="System overview" width="800">
</p>

## Project status

> **Proof of concept.** This project is early-stage. Algorithms are based on established vibration-analysis methods, but full industrial validation is still in progress. Do **not** use outputs as the sole basis for safety-critical maintenance decisions without independent engineering verification.

> **Independence disclaimer.** This is an independent open-source project, not affiliated with or endorsed by Anthropic or STMicroelectronics. Product names are used for interoperability context only.

## Why this exists

Industrial predictive maintenance typically requires fragmented tools and deep specialist knowledge. This project provides a reproducible, extensible way to:

- acquire vibration data from edge MEMS sensors (currently STWIN.box, extensible to other boards),
- analyze signals through explicit DSP and fault-detection heuristics,
- expose those capabilities as MCP tools any LLM client can invoke, and
- orchestrate end-to-end diagnostic workflows in natural language via Claude Skills.

## Quick start

```bash
# Clone
git clone https://github.com/LGDiMaggio/claude-stwinbox-diagnostics.git && cd claude-stwinbox-diagnostics

# Install both MCP servers
uv pip install -e mcp-servers/stwinbox-sensor-mcp -e mcp-servers/vibration-analysis-mcp
```

Then configure your MCP client (Claude Desktop, Claude Code, or compatible runtime) as documented in [docs/getting-started.md](docs/getting-started.md).

## Components

### MCP servers

| Server                                                     | Purpose                                                                                                     | Key tools                                                                                                                                                                                                               |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [stwinbox-sensor-mcp](mcp-servers/stwinbox-sensor-mcp/)       | Sensor acquisition via STWIN.box USB-HID or USB-Serial                                                      | `datalog2_connect`, `datalog2_start_acquisition`, `datalog2_stop_acquisition`, `datalog2_list_sensors`, `datalog2_configure_sensor`, `connect_board`, `acquire_data`, `load_data_from_file`             |
| [vibration-analysis-mcp](mcp-servers/vibration-analysis-mcp/) | Signal processing and fault detection. Works with any vibration data: CSV, NumPy, WAV, or DATALOG2 folders. | `load_signal`, `list_stored_signals`, `compute_fft_spectrum`, `compute_envelope_spectrum`, `check_bearing_fault_peak`, `check_bearing_faults_direct`, `diagnose_vibration`, `assess_vibration_severity` |

### Claude Skills

| Skill                                                             | Purpose                                            |
| ----------------------------------------------------------------- | -------------------------------------------------- |
| [machine-vibration-monitoring](skills/machine-vibration-monitoring/) | Sensor acquisition and baseline/threshold workflow |
| [vibration-fault-diagnosis](skills/vibration-fault-diagnosis/)       | Multi-step fault diagnosis with frequency analysis |
| [operator-diagnostic-report](skills/operator-diagnostic-report/)     | Human-readable maintenance report generation       |

## Supported fault types

| Fault                         | Detection method  | Indicators             |
| ----------------------------- | ----------------- | ---------------------- |
| Bearing inner race (BPFI)     | Envelope analysis | Harmonics of BPFI      |
| Bearing outer race (BPFO)     | Envelope analysis | Harmonics of BPFO      |
| Bearing rolling element (BSF) | Envelope analysis | Harmonics of BSF       |
| Bearing cage (FTF)            | Envelope analysis | Harmonics of FTF       |
| Unbalance                     | FFT               | 1x RPM dominant        |
| Misalignment                  | FFT               | 1x and 2x RPM          |
| Mechanical looseness          | FFT               | Multiple RPM harmonics |

## Hardware reference (STWIN.box)

The reference hardware is the [STEVAL-STWINBX1](https://www.st.com/en/evaluation-tools/steval-stwinbx1.html), but the analysis server accepts data from any source.

| Sensor     | Type                 | Typical use                        |
| ---------- | -------------------- | ---------------------------------- |
| IIS3DWB    | 3-axis accelerometer | Wideband vibration monitoring      |
| ISM330DHCX | 6-axis IMU           | Medium-frequency vibration         |
| IMP23ABSU  | Analog microphone    | Acoustic and ultrasound indicators |
| STTS22H    | Temperature          | Thermal context                    |
| ILPS22QS   | Pressure             | Environmental context              |

## Architecture

Two MCP servers expose sensor acquisition and signal analysis as tool calls. Three Claude Skills orchestrate them into monitoring, diagnosis, and reporting workflows. Data can come from live USB acquisition or pre-recorded files in multiple formats.

See [docs/architecture.md](docs/architecture.md) for diagrams, data flow, and project structure.

## Who this is for

- **Developers** building MCP-enabled industrial AI workflows.
- **Researchers** exploring LLM-assisted diagnostics and human-in-the-loop condition monitoring.
- **System integrators** evaluating conversational maintenance interfaces on edge sensor stacks.

## Documentation

| Resource                | Link                                                          |
| ----------------------- | ------------------------------------------------------------- |
| Getting started         | [docs/getting-started.md](docs/getting-started.md)               |
| Architecture            | [docs/architecture.md](docs/architecture.md)                     |
| Examples                | [examples/README.md](examples/README.md)                         |
| Contributing            | [CONTRIBUTING.md](CONTRIBUTING.md)                               |
| Roadmap                 | [docs/roadmap.md](docs/roadmap.md)                               |
| Security policy         | [SECURITY.md](SECURITY.md)                                       |
| Consistency governance  | [docs/consistency-governance.md](docs/consistency-governance.md) |
| Third-party attribution | [NOTICE](NOTICE)                                                 |

## Citation

If you use this project in research or technical reports, please cite:

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

## License

Licensed under Apache License 2.0. See [LICENSE](LICENSE).
