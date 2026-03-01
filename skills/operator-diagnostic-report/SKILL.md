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

## ⛔ Data Integrity Rules — MANDATORY

These rules override everything else. Violating them produces a misleading report.

### NEVER invent metadata the user has not provided

- **Machine name**: Use the value the user stated. If unknown → write "Not specified".
- **Machine location**: Use the value the user stated. If unknown → write "Not specified".
- **Operator / analyst name**: Use the value the user stated. If unknown → omit the field.
- **RPM / shaft speed**: Use the value the user stated **or** the value returned by
  `diagnose_vibration`. If unknown → write "Unknown — not provided by operator".
- **Bearing type**: Only include if the user provided a bearing designation or geometry.

Do NOT fill template placeholders (`{machine_location}`, `{machine_name}`, etc.)
with guessed or hallucinated values. If a placeholder has no data, replace it
with "Not specified" or remove the row entirely.

### NEVER present hypotheses as confirmed findings

If `diagnose_vibration` was called **without RPM**, the tool cannot identify
shaft-frequency faults (unbalance, misalignment, looseness). The report must:
1. State clearly: "Shaft speed was not provided; shaft-frequency analysis was not performed."
2. Report only the data the tool actually returned (RMS, kurtosis, crest factor, ISO severity, spectral peaks).
3. NOT add fault diagnoses that the tool did not produce (e.g. do not write
   "possible unbalance" if the tool never returned an unbalance diagnosis).

If bearing data was not provided, do NOT add bearing fault hypotheses.

### Distinguish MCP tool output from general knowledge

When including information based on your general engineering knowledge
(e.g. typical RPM ranges, ISO 1940 balancing grades, common maintenance
procedures) rather than MCP tool output, you **MUST** clearly label it:

> ⚠️ **Note — general engineering knowledge**: This recommendation is based on
> standard engineering practice, not on data from the MCP analysis tools.

Never present general knowledge as if it were a finding from sensor data analysis.

---

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

## PDF Generation with ReportLab

When the user asks for a PDF report, generate a Python script using `reportlab`.
Follow these **mandatory** rules to avoid layout issues:

### Table Layout — Preventing Text Overflow

**CRITICAL**: Long text in table cells **must** wrap. Never use a plain string
in a cell if it might exceed the column width — it will overlap adjacent cells.

```python
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

styles = getSampleStyleSheet()
cell_style = styles["BodyText"]  # word-wraps automatically

# ALWAYS wrap cell text in Paragraph() if it might be long
data = [
    ["#", "Finding", "Severity", "Action"],
    [
        "1",
        Paragraph("Impulsive axial vibration detected on Z-axis with elevated kurtosis", cell_style),
        "Monitor",
        Paragraph("Schedule bearing inspection within 30 days", cell_style),
    ],
]

# ALWAYS set explicit colWidths so text wraps within each column
col_widths = [0.3*inch, 2.5*inch, 0.8*inch, 2.5*inch]
table = Table(data, colWidths=col_widths)
table.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("WORDWRAP", (0, 0), (-1, -1), True),
]))
```

### Rules summary
1. **Always set `colWidths`** — never let ReportLab auto-size columns
2. **Wrap long text in `Paragraph(text, style)`** — plain strings don't wrap
3. **Use `VALIGN=TOP`** so multi-line cells align properly
4. Use the page width (letter = 7.5 inch usable) to calculate proportional widths
5. For the findings table: col widths ≈ [0.3, 2.5, 0.8, 0.8, 2.5] inches

### Section 5 — Detailed Findings Tables (CRITICAL)

The "Detailed Findings" section generates the worst layout problems because each
finding has long descriptive text. Apply **all** of these rules:

```python
from reportlab.lib import colors

# 1. Header cells: dark background + white bold text for contrast
header_style = ParagraphStyle("TableHeader", parent=styles["BodyText"],
                              textColor=colors.white, fontName="Helvetica-Bold",
                              fontSize=9)
body_style = ParagraphStyle("TableBody", parent=styles["BodyText"],
                            fontSize=8, leading=10)

# 2. EVERY cell must be a Paragraph — no plain strings
header_row = [
    Paragraph("#", header_style),
    Paragraph("Finding", header_style),
    Paragraph("Severity", header_style),
    Paragraph("Confidence", header_style),
    Paragraph("Action Required", header_style),
]
data_row = [
    Paragraph("1", body_style),
    Paragraph("Impulsive axial vibration detected…", body_style),
    Paragraph("Monitor", body_style),
    Paragraph("Medium", body_style),
    Paragraph("Schedule bearing inspection within 30 days", body_style),
]

# 3. Explicit column widths (must sum ≤ 7.5 inches)
col_widths = [0.3*inch, 2.3*inch, 0.7*inch, 0.7*inch, 2.5*inch]

table = Table([header_row, data_row], colWidths=col_widths)
table.setStyle(TableStyle([
    # Dark header row
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    # Alternating row shading for readability
    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F3F4")]),
    # Grid and alignment
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("WORDWRAP", (0, 0), (-1, -1), True),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
```

**Common mistakes to avoid in Section 5:**
- ❌ Plain strings in cells → text overflows into adjacent columns
- ❌ No header background → header indistinguishable from body
- ❌ Missing `colWidths` → columns auto-size and overflow the page
- ❌ No grid lines → rows blend together
- ❌ Font size too large → text wraps excessively or overflows

### Report Footer

Always end the PDF with this footer text:

```
Report generated automatically by Claude Edge Predictive Maintenance
Sensor: STEVAL-STWINBX1 | Firmware: FP-SNS-DATALOG2 | Analysis: vibration-analysis-mcp
```

Do NOT use the old wording "STWIN.box + Claude vibration diagnostics system".

## Evidence & Assumptions Protocol

When presenting results, always separate:
1. **Measured evidence** (tool outputs, frequencies, amplitudes, ISO zone, statistics)
2. **Inference** (diagnostic interpretation with confidence)
3. **Assumptions / prior knowledge** (catalog values, typical fault heuristics, missing machine metadata)

If assumptions are used because required inputs are missing, declare this explicitly and ask for the missing data when practical.

