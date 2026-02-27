---
name: machine-vibration-monitoring
description: |
  WHAT: Connects to the STEVAL-STWINBX1 sensor board to acquire vibration data,
  configure MEMS sensors, and establish baseline vibration profiles for rotating machinery.
  WHEN: Use when the user wants to start monitoring a machine, acquire vibration data from
  the STWIN.box, configure sensor parameters, or compare current vibration levels against
  a stored baseline.
dependencies:
  mcpServers:
    - stwinbox-sensor-mcp
    - vibration-analysis-mcp
tags:
  - vibration
  - condition-monitoring
  - STWIN.box
  - MEMS-sensors
  - industrial
---

# Machine Vibration Monitoring

You are helping the user set up and operate vibration-based condition monitoring
on rotating machinery using the **STEVAL-STWINBX1 (STWIN.box)** sensor node.

## System Architecture

The STWIN.box is an industrial-grade sensor node with these relevant sensors:
- **IIS3DWB**: 3-axis wideband accelerometer, up to 26.7 kHz bandwidth — primary sensor for vibration
- **ISM330DHCX**: 6-axis IMU with machine-learning core, up to 6.7 kHz
- **IIS2ICLX**: High-accuracy 2-axis inclinometer
- **STTS22H**: Temperature sensor (±0.5 °C accuracy)

The board communicates over USB serial. Two MCP servers handle acquisition and analysis.

## Workflow: First-Time Setup

When a user wants to monitor a new machine, follow these steps:

1. **Connect to the board**
   - Use `list_serial_ports` to find available COM ports
   - Use `connect_board` with the correct port and baud rate (default 115200)
   - Use `get_board_info` to confirm firmware and board identity

2. **Configure sensors for the application**
   - Ask the user about the machine type and expected shaft speed (RPM)
   - Use `recommend_sensor_config` with the shaft RPM to get optimal settings
   - Or use `list_sensor_presets` and `apply_preset` for quick setup
   - Common presets:
     - `wideband_vibration` — IIS3DWB at 26667 Hz, best for bearing analysis
     - `medium_vibration` — ISM330DHCX at 6667 Hz, good general purpose
     - `low_speed_vibration` — ISM330DHCX at 833 Hz, for slow machines <120 RPM

3. **Acquire baseline data**
   - Use `acquire_data` with appropriate duration (recommend ≥2 seconds for good frequency resolution)
   - Compute the FFT using `compute_fft_spectrum` from the vibration-analysis server
   - Assess severity with `assess_vibration_severity` (ISO 10816)
   - Store / present this as the baseline vibration signature

## Workflow: Routine Monitoring

1. Connect and acquire data (same sensor config as baseline)
2. Compute FFT and compare spectral peaks against baseline
3. Flag any new peaks or amplitude increases >6 dB (factor of 2)
4. Report ISO 10816 severity zone

## Key Guidance

- Always specify the **axis** when discussing vibration (X = horizontal, Y = vertical, Z = axial on typical installations)
- Vibration amplitude in **g** (acceleration) or **mm/s** (velocity) — clarify units
- Frequency resolution = sample_rate / N_samples. For 1 Hz resolution at 26667 Hz sample rate you need 26667 samples (~1 second)
- The IIS3DWB is the preferred sensor for bearing fault detection due to its high bandwidth
- The ISM330DHCX is suitable for general unbalance/misalignment detection
- Temperature from STTS22H can help correlate vibration changes with thermal effects

## Sensor Configuration Reference

See [sensor-specs.md](references/sensor-specs.md) for detailed sensor specifications
and recommended ODR (Output Data Rate) settings for different use cases.

## Example Interaction

**User**: "I want to start monitoring the vibration on our pump"

**Response approach**:
1. Ask about the pump type, RPM, and bearing information if known
2. Connect to the STWIN.box
3. Apply the recommended sensor preset
4. Acquire a baseline measurement
5. Present the FFT spectrum and ISO 10816 assessment
6. Suggest a monitoring interval
