# Vibration Fault Signature Reference

## Shaft-Related Faults

### Unbalance
- **Spectral signature**: Dominant peak at 1× shaft frequency
- **Direction**: Primarily radial (horizontal and vertical)
- **Phase**: Single reference mark per revolution, stable phase
- **Distinguishing features**:
  - 1× amplitude >> 2× amplitude (ratio typically > 3:1)
  - Vertical and horizontal 1× amplitudes similar in magnitude
  - Phase difference between H and V approximately 90°
- **Severity indication**: Proportional to unbalance mass × radius × ω²

### Parallel (Offset) Misalignment
- **Spectral signature**: Elevated 2× shaft frequency, often 1× also present
- **Direction**: Radial (perpendicular to shaft axis)
- **Distinguishing features**:
  - 2× amplitude > 50% of 1× amplitude
  - Axial component may also be elevated
  - Phase: 180° across coupling in radial direction

### Angular Misalignment
- **Spectral signature**: Strong 1× in axial direction, 2× also present
- **Direction**: Axial dominant
- **Distinguishing features**:
  - Axial 1× > radial 1×
  - 180° phase across coupling in axial direction
  - Often accompanied by 2× and 3×

### Mechanical Looseness

#### Type A — Structural looseness (soft foot)
- **Signature**: 1× dominant, directional
- **Key indicator**: Phase unstable, changes with bolt tightening

#### Type B — Bearing housing looseness
- **Signature**: Multiple harmonics of shaft speed (1×, 2×, 3×, ...)
- **Key indicator**: Sub-harmonics (0.5×) may appear, truncated waveform

#### Type C — Bearing-to-shaft looseness
- **Signature**: Many harmonics, noisy spectrum floor
- **Key indicator**: Broad spectral "haystack", random amplitude variation

## Bearing Faults

### Outer Race Defect (BPFO)
- **Envelope spectrum**: Peaks at BPFO and harmonics (2×BPFO, 3×BPFO)
- **Modulation**: May show sidebands at FTF (cage frequency)
- **Progression**:
  1. Early: only visible in envelope spectrum, high-frequency resonance bands
  2. Moderate: visible in direct FFT as BPFO harmonics
  3. Severe: broadband noise increase, random vibration

### Inner Race Defect (BPFI)
- **Envelope spectrum**: Peaks at BPFI and harmonics
- **Modulation**: Sidebands at 1× shaft frequency (because defect rotates with shaft)
- **Distinguishing from BPFO**: Shaft-speed modulation is the key difference

### Ball/Roller Defect (BSF)
- **Envelope spectrum**: Peaks at 2×BSF (ball spin creates impact twice per revolution)
- **Modulation**: Sidebands at FTF
- **Note**: BSF is less commonly detected than BPFO/BPFI

### Cage Defect (FTF)
- **Where**: Low frequency (FTF is typically 0.35–0.45 × shaft frequency)
- **Signature**: Peak at FTF, sub-synchronous
- **Note**: Cage faults are rare but potentially catastrophic

### Bearing Frequency Formulas
```
f_shaft = RPM / 60

FTF  = f_shaft × 0.5 × (1 − Bd/Pd × cos α)
BPFO = f_shaft × N/2 × (1 − Bd/Pd × cos α)
BPFI = f_shaft × N/2 × (1 + Bd/Pd × cos α)
BSF  = f_shaft × Pd/(2×Bd) × (1 − (Bd/Pd × cos α)²)
```
Where: N = number of balls, Bd = ball diameter, Pd = pitch diameter, α = contact angle

## Gear Faults

### Gear Mesh Frequency
- **GMF** = number_of_teeth × shaft_frequency
- **Healthy**: GMF peak present, low sidebands
- **Fault**: Sidebands at shaft frequency around GMF, increasing with severity
- **Broken tooth**: Impact once per revolution → sidebands spaced at shaft frequency, time-domain impulse

## Electrical Faults (Motor-Specific)

### Rotor Bar Faults
- **Frequency**: Peaks at f_line × (1 ± 2s) where s = slip
- **Pole pass frequency**: 2 × s × f_line
- **Note**: Slip frequency is typically 1–3% of synchronous speed

### Stator Eccentricity
- **Frequency**: 2× line frequency (100/120 Hz)
- **Distinguishing from misalignment**: Does not change with shaft speed

## Vibration Severity Quick Reference (ISO 10816)

| Zone | Group 2 (15–300 kW) | Group 4 (<15 kW) | Interpretation |
|------|---------------------|-------------------|----------------|
| A    | ≤ 1.4 mm/s         | ≤ 0.71 mm/s      | Good           |
| B    | ≤ 2.8 mm/s         | ≤ 1.8 mm/s       | Acceptable     |
| C    | ≤ 7.1 mm/s         | ≤ 4.5 mm/s       | Alarm          |
| D    | > 7.1 mm/s         | > 4.5 mm/s       | Danger         |
