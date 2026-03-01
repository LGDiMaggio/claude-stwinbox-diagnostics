---
name: machine-vibration-monitoring
description: |
  WHAT: Connects to the STEVAL-STWINBX1 sensor board to acquire vibration data,
  configure MEMS sensors, and establish baseline vibration profiles for rotating machinery.
  WHEN: Use when the user wants to start monitoring a machine, acquire vibration data from
  the STWIN.box, configure sensor parameters, set up data logging, or compare current
  vibration levels against a stored baseline. Also use for "connect to sensor",
  "acquire vibration", "set up monitoring", or "configure STWIN".
metadata:
  author: LGDiMaggio
  version: 2.0.0
  servers: stwinbox-sensor-mcp, vibration-analysis-mcp
  tags: vibration, condition-monitoring, STWIN.box, MEMS-sensors, industrial
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

The board runs **FP-SNS-DATALOG2** firmware and communicates over **USB-HID**.
Two MCP servers handle acquisition and analysis.

## Available MCP Tools

### Sensor Server (stwinbox-sensor-mcp)
- `datalog2_connect` — Connect via USB-HID
- `datalog2_start_acquisition(name, description, duration_s)` — Start logging; `duration_s` auto-stops
- `datalog2_stop_acquisition` — Stop manual-mode acquisition
- `datalog2_get_device_info` — Device/firmware info
- `datalog2_list_sensors` — Active sensors with ODR/FS
- `datalog2_configure_sensor` — Enable/disable, set ODR/FS
- `datalog2_tag_acquisition` — Add event tags during acquisition

### Analysis Server (vibration-analysis-mcp)
- `load_signal` — Load data from file or DATALOG2 acquisition folder
- `compute_fft_spectrum` — FFT magnitude spectrum
- `find_spectral_peaks` — Detect dominant frequency peaks
- `assess_vibration_severity` — ISO 10816 severity classification
- `diagnose_vibration` — Full automated diagnosis pipeline

## Workflow: First-Time Setup

When a user wants to monitor a new machine, follow these steps:

1. **Connect to the board**
   - `datalog2_connect` — auto-discovers the STWIN.box over USB-HID
   - `datalog2_get_device_info` — confirm firmware version and board identity

2. **Configure sensors for the application**
   - `datalog2_list_sensors` — see current sensor configuration (ODR, FS, enabled)
   - Ask the user about machine type and expected shaft speed (RPM)
   - `datalog2_configure_sensor` — enable/disable sensors, adjust ODR and full-scale
   - Typical configurations:
     - **Wideband vibration**: IIS3DWB at 26667 Hz ODR — best for bearing analysis
     - **General purpose**: ISM330DHCX at 6667 Hz — good for unbalance/misalignment

3. **Acquire baseline data**
   - `datalog2_start_acquisition(name="baseline", description="...", duration_s=5)`
     - The `duration_s` parameter auto-stops the acquisition server-side (no round-trip delay)
     - Returns the acquisition folder path
   - `load_signal(file_path="<acquisition_folder>", sensor_name="iis3dwb_acc")`
     - Sample rate is auto-detected from device config
   - `compute_fft_spectrum(data_id="...", channel="X")` — compute the FFT
   - `assess_vibration_severity(data_id="...", machine_group="group1")` — ISO 10816
   - Present this as the baseline vibration signature

## Workflow: Routine Monitoring

1. `datalog2_connect` → `datalog2_start_acquisition(duration_s=5)` → `load_signal`
2. `compute_fft_spectrum` and `find_spectral_peaks` — compare against baseline
3. Flag any new peaks or amplitude increases >6 dB (factor of 2)
4. `assess_vibration_severity` — report ISO 10816 severity zone

## Key Guidance

- Always specify the **axis** when discussing vibration (X = horizontal, Y = vertical, Z = axial on typical installations)
- Vibration amplitude in **g** (acceleration) or **mm/s** (velocity) — clarify units
- Frequency resolution = sample_rate / N_samples. For 1 Hz resolution at 26667 Hz sample rate you need 26667 samples (~1 second)
- The IIS3DWB is the preferred sensor for bearing fault detection due to its high bandwidth
- The ISM330DHCX is suitable for general unbalance/misalignment detection
- Temperature from STTS22H can help correlate vibration changes with thermal effects

## Units of Measurement

### Sensor output (IIS3DWB)
- Raw data: int16 (signed 16-bit)
- Sensitivity: 0.000122 g/LSB at ±16 g full-scale
- After SDK decoding: **acceleration in g** (gravity units, 1 g = 9.80665 m/s²)

### ISO 10816 assessment
- Requires **RMS velocity in mm/s** in the 10–1000 Hz band
- The `diagnose_vibration` tool converts acceleration (g) → velocity (mm/s)
  automatically via frequency-domain integration
- If using `assess_vibration_severity` directly, you **must** provide velocity
  in mm/s — do NOT pass raw acceleration in g

### Conversion chain
1. Raw int16 × sensitivity → acceleration in g
2. g × 9806.65 → acceleration in mm/s²
3. Frequency-domain integration (÷ j·2π·f) + band-pass 10–1000 Hz → velocity in mm/s
4. RMS of velocity → ISO 10816 input

## ⛔ Distinguish MCP Tool Output from General Knowledge

When providing information based on your general engineering knowledge
(e.g., typical speed ranges, recommended monitoring intervals, sensor
placement best practices) rather than MCP tool output, **MUST** label it:

> ⚠️ **General engineering knowledge** — not from sensor data analysis.

Never present textbook knowledge as if it came from the MCP analysis pipeline.

## ODR: Nominal vs Measured

When reporting sample rate after `load_signal`, you may see a slightly different
value than the configured ODR (e.g., 26,584 Hz instead of 26,667 Hz). This is
normal hardware behavior:

- **Nominal ODR** = configured value (26,667 Hz for IIS3DWB at ODR index 0)
- **Measured ODR** = actual rate from the crystal oscillator (~0.3% tolerance)

The measured ODR is used for analysis (more accurate FFT frequency bins). When
presenting results to the user, say:

> "Sample rate: 26,584 Hz (measured; nominal 26,667 Hz)"

Similarly, the acquisition duration may be slightly shorter in samples than the
wall-clock `duration_s` because the actual ODR is slightly lower. For example,
10 seconds at 26,584 Hz = 265,840 samples (~9.97 s at nominal). This is expected.

## Sensor Configuration Reference

See [sensor-specs.md](references/sensor-specs.md) for detailed sensor specifications
and recommended ODR (Output Data Rate) settings for different use cases.


## Evidence & Assumptions Protocol

When presenting results, always separate:
1. **Measured evidence** (tool outputs, frequencies, amplitudes, ISO zone, statistics)
2. **Inference** (diagnostic interpretation with confidence)
3. **Assumptions / prior knowledge** (catalog values, typical fault heuristics, missing machine metadata)

If assumptions are used because required inputs are missing, declare this explicitly and ask for the missing data when practical.

## Example Interaction

**User**: "I want to start monitoring the vibration on our pump"

**Response approach**:
1. Ask about the pump type, RPM, and bearing information if known
2. `datalog2_connect` to the STWIN.box
3. `datalog2_list_sensors` to check current config; adjust if needed
4. `datalog2_start_acquisition(name="pump_baseline", duration_s=5)`
5. `load_signal(file_path="<folder>", sensor_name="iis3dwb_acc")`
6. `compute_fft_spectrum` + `assess_vibration_severity`
7. Present the FFT spectrum and ISO 10816 assessment
8. Suggest a monitoring interval (e.g., weekly for Zone A/B, daily for Zone C)
