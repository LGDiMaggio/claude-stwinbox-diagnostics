# Diagnostic Report Guidelines

Reference material for generating effective maintenance diagnostic reports.

## Report Writing Best Practices

### Audience Awareness
Diagnostic reports serve multiple audiences with different needs:

| Audience | Needs | Language Level |
|----------|-------|----------------|
| **Machine operator** | What to do now, is it safe to run? | Plain language, no jargon |
| **Maintenance technician** | What to fix, what parts to order | Technical but actionable |
| **Reliability engineer** | Trend data, root cause analysis | Full technical detail |
| **Plant manager** | Cost impact, production risk, timeline | Business language |

Always write for the **least technical** audience first (Executive Summary), then
add detail in subsequent sections for more technical readers.

### Severity Communication

Use a consistent traffic-light system throughout:

| Icon | Zone | Label | Meaning |
|------|------|-------|---------|
| 🟢 | A | **Good** | Typical of newly commissioned machines |
| 🟡 | B | **Acceptable** | Suitable for unrestricted long-term operation |
| 🟠 | C | **Alarm** | Not suitable for long-term operation — plan maintenance |
| 🔴 | D | **Danger** | Risk of damage — take immediate action |

### Translating Technical Findings to Plain Language

Common fault types and how to describe them to operators:

| Technical Term | Operator-Friendly Description |
|---------------|-------------------------------|
| Unbalance (1× dominant) | "The rotating part has uneven weight distribution, causing vibration at the shaft speed" |
| Misalignment (2× elevated) | "The shaft is not properly aligned with the connected equipment, causing extra stress" |
| Mechanical looseness | "Something is loose — could be foundation bolts, bearing housing, or a structural component" |
| BPFI (inner race defect) | "Damage detected on the inner ring of the bearing — the part that rotates with the shaft" |
| BPFO (outer race defect) | "Damage detected on the outer ring of the bearing — the part pressed into the housing" |
| BSF (ball/roller defect) | "Damage detected on one or more rolling elements (balls or rollers) inside the bearing" |
| FTF (cage defect) | "Damage to the bearing cage — the component that keeps the rolling elements spaced apart" |
| High kurtosis / crest factor | "The vibration signal contains sharp impulses, often a sign of impacts inside a bearing or gear" |

### Actionable Recommendations

Every finding must include a **specific, actionable** recommendation. Avoid vague
statements like "monitor the situation". Instead:

**❌ Bad:** "Continue monitoring."  
**✅ Good:** "Increase measurement frequency to weekly. Schedule bearing replacement
within 30 days. Order SKF 6205-2RS bearing (quantity: 2)."

### Recommendation Priority Framework

| Priority | Criteria | Timeline |
|----------|----------|----------|
| **P1 — Immediate** | Zone D, or high-confidence bearing fault | Stop machine / act within 24h |
| **P2 — Urgent** | Zone C, or medium-confidence bearing fault | Plan within 1 week |
| **P3 — Planned** | Zone B trending toward C, or low-confidence fault | Schedule in next maintenance window |
| **P4 — Monitor** | Zone A/B stable, no faults detected | Continue routine monitoring |

## ISO 10816 Quick Reference

### Machine Groups

| Group | Description | Examples |
|-------|-------------|----------|
| **Group 1** | Large machines, rigid foundation, >300 kW | Large pumps, compressors, generators |
| **Group 2** | Medium machines, rigid foundation, 15–300 kW | Most industrial motors and pumps |
| **Group 3** | Large machines, flexible foundation | Turbine sets on spring isolators |
| **Group 4** | Small machines, <15 kW | Small fans, auxiliary pumps |

### Velocity Thresholds (mm/s RMS, 10–1000 Hz)

| Group | Zone A (Good) | Zone B (Acceptable) | Zone C (Alarm) | Zone D (Danger) |
|-------|:---:|:---:|:---:|:---:|
| Group 1 | ≤ 2.8 | ≤ 7.1 | ≤ 18.0 | > 18.0 |
| Group 2 | ≤ 1.4 | ≤ 2.8 | ≤ 7.1 | > 7.1 |
| Group 3 | ≤ 3.5 | ≤ 9.0 | ≤ 22.4 | > 22.4 |
| Group 4 | ≤ 0.71 | ≤ 1.8 | ≤ 4.5 | > 4.5 |

## Report Formatting Notes

- Always include **units** (mm/s, Hz, RPM, g)
- Use **tables** for structured data — easier to scan than paragraphs
- Include the **measurement date and conditions** — a report without context is useless
- If comparing to a baseline, state **when the baseline was taken** and under what conditions
- End with a clear **next step** — when to measure again, what additional tests are needed
