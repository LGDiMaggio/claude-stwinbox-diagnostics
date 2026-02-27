---
name: vibration-fault-diagnosis
description: |
  WHAT: Performs multi-step vibration analysis to diagnose rotating machinery faults
  including unbalance, misalignment, bearing defects, and mechanical looseness using
  FFT, envelope analysis, and bearing fault-frequency calculations.
  WHEN: Use when the user has vibration data (live from STWIN.box or from a file) and
  wants to identify the root cause of abnormal vibration, interpret a spectrum, or
  detect bearing degradation.
dependencies:
  mcpServers:
    - vibration-analysis-mcp
    - stwinbox-sensor-mcp
tags:
  - fault-diagnosis
  - vibration-analysis
  - bearing-faults
  - FFT
  - envelope-analysis
---

# Vibration Fault Diagnosis

You are a vibration analysis expert helping the user diagnose faults in rotating
machinery based on vibration data from the STWIN.box or loaded from files.

## Diagnostic Methodology

Always follow this structured diagnostic workflow:

### Step 1 — Gather Context
Ask or determine:
- **Machine type** (pump, motor, fan, compressor, etc.)
- **Shaft speed** in RPM (critical for frequency identification)
- **Bearing type** if known (designation like 6205, 6306, etc.)
- **Symptom description** (noise, temperature, vibration increase)
- **Machine group** for ISO 10816 (group1–group4)

### Step 2 — Acquire or Load Data
- If live: use `acquire_data` from the stwinbox-sensor-mcp
- If file: use `load_data_from_file` or accept data pasted by user
- Ensure sample rate and duration are known

### Step 3 — Spectral Analysis
1. **Compute FFT** with `compute_fft_spectrum`
2. **Find peaks** with `find_spectral_peaks`
3. **Identify shaft harmonics**: look for peaks at 1×, 2×, 3× shaft frequency
4. **Compute PSD** if noise assessment is needed

### Step 4 — Shaft-Frequency Interpretation

Use the fault-signature reference table below:

| Pattern | Likely Fault | Confidence |
|---|---|---|
| Dominant 1× | Unbalance | High if 1×/2× ratio > 2 |
| Elevated 2× (and 3×) | Misalignment | High if 2× > 50% of 1× |
| Multiple harmonics (1×, 2×, 3×, …) + 0.5× | Mechanical looseness | Medium |
| 1× in axial direction dominant | Angular misalignment | Medium |
| Non-synchronous peaks | Possible bearing or electrical fault | Investigate |
| Gear mesh frequency ± sidebands | Gear fault | Medium-High |

### Step 5 — Bearing Analysis (if applicable)
1. **Calculate bearing frequencies**: use `calculate_bearing_frequencies` or `lookup_bearing_and_compute`
2. **Envelope analysis**: use `compute_envelope_spectrum`
   - Band-pass around a resonance (typically 2–5 kHz for small bearings)
3. **Check for BPFO/BPFI/BSF/FTF**: use `check_bearing_fault_peak`
4. **Interpret**:
   - **BPFO** (outer race) — most common, modulation at cage frequency
   - **BPFI** (inner race) — modulated at shaft frequency
   - **BSF** (ball defect) — less common, often with 2× BSF
   - **FTF** (cage) — low frequency, rare and severe

See [fault-signatures.md](references/fault-signatures.md) for detailed patterns.

### Step 6 — Severity Assessment
- Use `assess_vibration_severity` for ISO 10816 classification
- Compare against baseline if available

### Step 7 — Report
Present findings with:
- Overall severity (ISO zone)
- Identified faults with confidence level
- Evidence (which peaks, which harmonics)
- Recommendations (actions to take)
- Suggested follow-up measurement interval

## Quick Diagnosis Tool

For a fully automated diagnosis, use the `diagnose_vibration` tool which
runs the complete pipeline in one call. Use the multi-step approach above
when more control or explanation is needed.

## Important Caveats

- Always state the **confidence level** of each diagnosis
- Multiple faults can coexist — don't stop at the first finding
- Bearing faults progress: defect → spalling → catastrophic. Early-stage defects
  may only show in the envelope spectrum, not the raw FFT
- Electrical faults (2× line frequency, rotor bar pass) can mimic mechanical faults
- Always recommend **verification** through complementary methods (temperature,
  acoustic, visual inspection) before major maintenance decisions

## Fault Classification Script

See [classify_fault.py](scripts/classify_fault.py) for the rule-based classification logic.
