---
name: operator-diagnostic-report
description: |
  WHAT: Generates structured diagnostic reports for machine operators and maintenance
  technicians, summarizing vibration analysis results with severity levels, fault
  findings, and actionable maintenance recommendations in clear, non-technical language.
  WHEN: Use when the user asks to create a report, generate a maintenance summary,
  produce documentation of a vibration measurement, or communicate findings to plant
  personnel. Also use for "write report", "summarize results", "generate PDF",
  or "create maintenance document".
metadata:
  author: LGDiMaggio
  version: 2.0.0
  servers: vibration-analysis-mcp
  tags: report-generation, maintenance, documentation, operator-friendly
---

# Operator Diagnostic Report

You are generating diagnostic reports for maintenance teams and machine operators.
Reports must be **clear, actionable, and accessible** to people who may not have
vibration analysis expertise.

## Tools Used for Report Data

The report is generated from the output of these analysis tools:
- `diagnose_vibration` — Run the full automated diagnosis first (RPM is optional;
  if unknown, the report will note that shaft-frequency analysis was not performed)
- `assess_vibration_severity` — ISO 10816 zone classification for the severity section
- `compute_fft_spectrum` / `find_spectral_peaks` — For spectral evidence in findings
- `load_signal` — To reference the measurement data source

## Report Structure

Always follow this template structure:

### 1. Header
- Report title
- Date and time of measurement
- Machine identification (name, tag, location)
- Technician / analyst name (if provided)

### 2. Executive Summary (2–3 sentences)
- Overall machine condition (Good / Acceptable / Alarm / Danger)
- Key finding in plain language
- Urgency level

### 3. Measurement Details
- Sensor used and mounting position (e.g., IIS3DWB accelerometer, magnetic mount)
- Sample rate and duration (auto-detected from DATALOG2 device config)
- Machine operating conditions (RPM if known, load state)
- Data source: DATALOG2 acquisition folder or imported file

### 4. Overall Vibration Severity
- ISO 10816 zone (A/B/C/D) with color indicator
- RMS velocity value and units
- Comparison to baseline (if available)
- Trend indication (improving / stable / degrading)

### 5. Findings Table
For each detected condition:

| # | Finding | Severity | Confidence | Action Required |
|---|---------|----------|------------|-----------------|
| 1 | ... | ... | ... | ... |

### 6. Detailed Analysis (for each finding)
- **What was detected**: Plain language description
- **Evidence**: The specific spectral features that indicate this
- **What it means**: Impact on machine operation and lifetime
- **Recommended action**: Specific maintenance steps

### 7. Recommendations Summary
Prioritized list of actions:
1. Immediate actions (Zone D / high confidence faults)
2. Planned maintenance (Zone C / medium confidence)
3. Monitoring adjustments (increase frequency, add measurement points)

### 8. Next Steps
- Recommended follow-up measurement date
- Additional tests if needed (alignment check, thermography, oil analysis)

## Language Guidelines

- Use **plain language** — avoid jargon where possible
- When technical terms are necessary, provide a brief explanation
  - Example: "BPFO (outer race bearing fault frequency)" → 
    "Vibration pattern indicating damage on the outer ring of the bearing"
- Use traffic-light colors for severity:
  - 🟢 Green = Good
  - 🟡 Yellow = Acceptable / Monitor
  - 🟠 Orange = Alarm / Plan maintenance
  - 🔴 Red = Danger / Act immediately
- Include specific numbers but always with context
  - Bad: "2× amplitude is 0.34 g"
  - Good: "Vibration at twice the shaft speed is elevated (0.34 g), which is typical of shaft misalignment"

## Report Template

See [report-template.md](assets/report-template.md) for the full Markdown template
that should be used to format the report output.

## Formatting Rules

- Output as **Markdown** (suitable for rendering or PDF conversion)
- Include tables for structured data
- Use horizontal rules to separate major sections
- Keep total report length reasonable (1–3 pages when printed)
- If multiple measurement points exist, show a summary table first,
  then detailed sections for each point with issues
