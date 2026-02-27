# ISO 10816 Vibration Severity Guide

## Overview

ISO 10816 (now largely replaced by ISO 20816, but widely referenced)
provides criteria for evaluating machine vibration severity based on
**broadband RMS velocity** in the **10–1000 Hz** frequency band.

## Machine Groups

### Group 1 — Large machines on rigid foundations (>300 kW or >200 kW electric machines)
Examples: Large pumps, turbines, generators, compressors on concrete plinths.

### Group 2 — Medium machines on rigid foundations (15–300 kW)
Examples: Standard electric motors, fans, centrifugal pumps.

### Group 3 — Large machines on flexible foundations
Examples: Turbogenerators on steel frames, large fans on elevated platforms.

### Group 4 — Small machines (<15 kW)
Examples: Small motors, auxiliary equipment, fractional-HP pumps.

## Severity Zones

| Zone | Description | Action |
|------|------------|--------|
| **A** | Good | Vibration of newly commissioned machines |
| **B** | Acceptable | Long-term operation is acceptable |
| **C** | Alarm | Not suitable for long-term continuous operation. Investigate and plan maintenance. |
| **D** | Danger | Vibration severe enough to cause damage. Stop machine as soon as safely possible. |

## Threshold Values (RMS velocity, mm/s, 10–1000 Hz)

| Boundary | Group 1 | Group 2 | Group 3 | Group 4 |
|----------|---------|---------|---------|---------|
| A/B      | 2.8     | 1.4     | 3.5     | 0.71    |
| B/C      | 7.1     | 2.8     | 9.0     | 1.8     |
| C/D      | 18.0    | 7.1     | 22.4    | 4.5     |

## Measurement Guidelines

- **Location**: Measure on bearing housings, as close to the bearing as possible
- **Direction**: Measure in three orthogonal directions (H, V, A)
- **Condition**: Machine at normal operating speed and load
- **Mounting**: Sensor firmly mounted (stud > adhesive > magnet > hand-held)
- **Frequency range**: 10–1000 Hz for standard assessment
  - Extended range (2–10000 Hz) for high-speed machines or bearing analysis
- **Parameter**: RMS velocity (mm/s or in/s)

## Converting Between Units

| From | To | Formula |
|------|----|---------|
| Acceleration (g peak) | Velocity (mm/s RMS) | v = (a × 9810) / (2π × f × √2) |
| Acceleration (m/s² RMS) | Velocity (mm/s RMS) | v = (a × 1000) / (2π × f) |
| Velocity (mm/s RMS) | Displacement (µm peak) | d = v × √2 × 1000 / (2π × f) |
| in/s peak | mm/s RMS | multiply by 25.4 / √2 ≈ 17.96 |

Note: These conversions are exact only at a single frequency. For broadband signals,
integration (velocity from acceleration) should be done in the frequency domain.

## Trending Rules of Thumb

- **Baseline**: Establish within 1 week of commissioning or after maintenance
- **Alert**: >25% increase from baseline (consider investigating)
- **Alarm**: >50% increase or zone change (B→C)
- **Danger**: Absolute Zone D or >100% increase
- **Trending interval**:
  - Zone A: monthly
  - Zone B: weekly to bi-weekly
  - Zone C: daily to every few days
  - Zone D: continuous monitoring / stop machine
