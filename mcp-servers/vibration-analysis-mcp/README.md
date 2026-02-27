# vibration-analysis-mcp

MCP Server for **vibration signal processing and rotating machinery fault detection**.

## Features

- FFT (Fast Fourier Transform) and Power Spectral Density
- Envelope analysis (Hilbert transform) for bearing fault detection
- Order spectrum computation relative to machine RPM
- Bearing characteristic frequency calculation (BPFI, BPFO, BSF, FTF)
- Automated fault detection and classification
- ISO 10816 vibration severity assessment
- Time-domain statistics (RMS, peak, crest factor, kurtosis)

## Installation

```bash
uv venv && uv pip install -e .
```

## Available Tools

| Tool | Description |
|------|-------------|
| `compute_fft_spectrum` | Compute single-sided FFT amplitude spectrum |
| `compute_power_spectral_density` | Power Spectral Density via Welch method |
| `compute_spectrogram_stft` | Short-Time Fourier Transform spectrogram |
| `find_spectral_peaks` | Find dominant peaks in a frequency spectrum |
| `compute_envelope_spectrum` | Hilbert envelope analysis for bearing faults |
| `check_bearing_fault_peak` | Check bearing fault frequency in envelope spectrum |
| `calculate_bearing_frequencies` | Calculate BPFI/BPFO/BSF/FTF from geometry |
| `lookup_bearing_and_compute` | Look up bearing by designation + compute frequencies |
| `list_known_bearings` | List built-in bearing database |
| `assess_vibration_severity` | ISO 10816 vibration severity classification |
| `diagnose_vibration` | Full automated diagnosis pipeline |

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
