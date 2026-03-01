# vibration-analysis-mcp

MCP Server for **vibration signal processing and rotating machinery fault detection**.

## Features

- **Server-side signal store** — signals loaded once, never transit the conversation
- FFT (Fast Fourier Transform) and Power Spectral Density (Welch)
- Short-Time Fourier Transform (STFT) spectrogram
- Envelope analysis (Hilbert transform) for bearing fault detection
- Bearing characteristic frequency calculation (BPFI, BPFO, BSF, FTF)
- Direct bearing fault check with manufacturer catalog frequencies
- Automated fault detection and classification
- ISO 10816 vibration severity assessment
- Time-domain statistics (RMS, peak, crest factor, kurtosis)
- DATALOG2 acquisition folder loading (auto-detects ODR from device config)

## Installation

```bash
uv venv && uv pip install -e .
```

## Available Tools

### Signal Store

| Tool | Description |
|------|-------------|
| `load_signal` | Load a .csv/.dat file or DATALOG2 acquisition folder into the server-side store |
| `list_stored_signals` | List all stored signals with statistics (RMS, peak, kurtosis, duration) |

### Spectral Analysis

| Tool | Description |
|------|-------------|
| `compute_fft_spectrum` | Compute single-sided FFT amplitude spectrum |
| `compute_power_spectral_density` | Power Spectral Density via Welch method |
| `compute_spectrogram_stft` | Short-Time Fourier Transform spectrogram |
| `find_spectral_peaks` | Find dominant peaks in a frequency spectrum |

### Bearing Analysis

| Tool | Description |
|------|-------------|
| `compute_envelope_spectrum` | Hilbert envelope analysis for bearing faults |
| `check_bearing_fault_peak` | Check a single bearing fault frequency in envelope spectrum |
| `check_bearing_faults_direct` | Check BPFO/BPFI/BSF/FTF using frequencies from manufacturer catalogs (no geometry needed) |
| `calculate_bearing_frequencies` | Calculate BPFI/BPFO/BSF/FTF from bearing geometry |
| `lookup_bearing_and_compute` | Look up bearing by designation + compute frequencies |
| `list_known_bearings` | List built-in bearing database |

### Diagnosis & Severity

| Tool | Description |
|------|-------------|
| `assess_vibration_severity` | ISO 10816 vibration severity classification |
| `diagnose_vibration` | Full automated diagnosis pipeline (RPM optional) |

## Fault Detection Capabilities

| Fault | Method | Key Signatures |
|-------|--------|---------------|
| Bearing inner race | Envelope analysis | BPFI × N harmonics |
| Bearing outer race | Envelope analysis | BPFO × N harmonics |
| Bearing ball defect | Envelope analysis | BSF × N harmonics |
| Unbalance | FFT at 1× RPM | Dominant 1× component |
| Misalignment | FFT | Strong 1× and 2× RPM |
| Mechanical looseness | FFT | Multiple RPM harmonics |
| Gear mesh faults | FFT | GMF ± RPM sidebands |
