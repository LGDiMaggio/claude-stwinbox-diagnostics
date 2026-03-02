# Consistency & Evidence Governance

This document defines project-wide checks to keep diagnostics coherent across physics, formal methods, and generated outputs.

## 1) Physical-Model Consistency

Use this checklist before accepting a diagnostic conclusion:

- **Units are explicit and preserved end-to-end**:
  - Acceleration: `g` (or `m/s²` only with conversion declared)
  - Velocity severity: `mm/s RMS` for ISO 10816 tools
  - Frequency: `Hz`; speed: `RPM`
- **Sampling assumptions are consistent**:
  - Use measured sample rate returned by `load_signal` for FFT/envelope bins
  - State nominal vs measured ODR when they differ
- **Transforms are context-driven, not arbitrary**:
  - FFT/PSD for synchronous shaft patterns (1×, 2×, harmonics)
  - Envelope spectrum for rolling-element bearing faults
  - STFT when non-stationarity is relevant
- **Filter choices are justified**:
  - Band-pass ranges for envelope analysis must be tied to resonance expectations (e.g., 2–5 kHz for small bearings)

## 2) Formal Coherence

- Tool names in docs must match executable entry points (`stwinbox_sensor_mcp`, `vibration_analysis_mcp`).
- Workflow order must match server behavior (acquire -> load -> analyze -> interpret).
- Claims in READMEs and skills must be reproducible with available MCP tools.

## 3) Evidence-First Output Policy

Every diagnostic response should separate:

1. **Observed evidence** (tool outputs, peaks, ISO zone, statistics)
2. **Inference** (fault hypothesis with confidence)
3. **External/domain priors** (catalog values, engineering heuristics)

If inference uses prior knowledge not directly measured in the current dataset, state it explicitly as an assumption.

## 4) "Divieti" (Prohibitions) Policy

To avoid opaque restrictions accumulating over iterations:

- Keep only prohibitions that prevent unsafe or invalid analysis (e.g., do not invent missing RPM).
- Pair each prohibition with rationale and fallback behavior.
- Prefer positive operating rules ("do X when Y") over blanket bans.

## 5) STM Documentation Alignment

Reference baseline sources when evolving the project:

- ST UM2965 user manual (board and sensor capabilities)
- FP-SNS-DATALOG2 workflows and constraints
- FP-AI-MONITOR context only when explicitly used

When repository guidance diverges from ST documentation, document the reason and scope (e.g., "legacy serial fallback").

## 6) Internal Documentation Coherence

Perform a quick coherence pass on changes to README/docs/skills:

- Firmware recommendation is consistent across files
- Preferred acquisition path is consistent (USB-HID DATALOG2 first)
- Tool and command names are identical everywhere
- Severity standard wording is consistent (`ISO 10816` in current implementation)

## 7) Suggested Maintenance Cadence

- Run a docs coherence review at each release tag.
- Capture known assumptions in one place (this file) and reference it from top-level README.
