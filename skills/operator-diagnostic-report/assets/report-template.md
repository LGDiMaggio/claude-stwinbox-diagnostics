# Machine Vibration Diagnostic Report

---

**Report ID**: `{report_id}`  
**Date**: {date}  
**Machine**: {machine_name}  
**Location**: {machine_location}  
**Analyst**: {analyst_name}

---

## Executive Summary

{severity_icon} **Overall Condition: {overall_condition}**

{executive_summary_text}

---

## Measurement Details

| Parameter | Value |
|-----------|-------|
| Sensor | {sensor_name} |
| Mounting point | {mounting_point} |
| Sample rate | {sample_rate} Hz |
| Duration | {duration} seconds |
| Shaft speed | {rpm} RPM ({shaft_freq} Hz) |
| Operating load | {load_condition} |

---

## Vibration Severity (ISO 10816)

| Parameter | Value | Zone |
|-----------|-------|------|
| RMS Velocity | {rms_velocity} mm/s | {iso_zone_icon} Zone {iso_zone} |
| Machine Group | {machine_group_desc} | |
| Baseline | {baseline_value} mm/s | Zone {baseline_zone} |
| Change | {change_pct}% | {trend_icon} {trend_desc} |

**Zone interpretation:**
- 🟢 **Zone A** (≤{threshold_ab} mm/s) — Good: typical of new machines
- 🟡 **Zone B** (≤{threshold_bc} mm/s) — Acceptable for long-term operation
- 🟠 **Zone C** (≤{threshold_cd} mm/s) — Alarm: investigate, plan maintenance
- 🔴 **Zone D** (>{threshold_cd} mm/s) — Danger: risk of damage

---

## Findings

| # | Condition | Severity | Confidence | Action |
|---|-----------|----------|------------|--------|
{findings_table_rows}

---

## Detailed Analysis

{detailed_findings_sections}

---

## Recommendations

### Immediate Actions
{immediate_actions}

### Planned Maintenance
{planned_maintenance}

### Monitoring Adjustments
{monitoring_adjustments}

---

## Next Steps

- **Next measurement**: {next_measurement_date}
- **Additional tests**: {additional_tests}
- **Notes**: {notes}

---

*Report generated with STWIN.box + Claude vibration diagnostics system*  
*Sensor: STEVAL-STWINBX1 | Analysis: vibration-analysis-mcp v0.1.0*
