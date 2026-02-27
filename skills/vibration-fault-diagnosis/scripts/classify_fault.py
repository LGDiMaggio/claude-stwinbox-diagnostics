"""
classify_fault.py — Rule-based fault classification from spectral features.

This script applies the same logic as the vibration-analysis-mcp fault_detection
module, but can be run standalone by Claude for quick classification without
needing the full MCP server.

Input (via stdin JSON):
{
    "shaft_freq_hz": 25.0,
    "spectrum_peaks": [
        {"frequency_hz": 25.0, "amplitude": 0.45},
        {"frequency_hz": 50.0, "amplitude": 0.12},
        ...
    ],
    "kurtosis": 3.1,
    "crest_factor": 3.5,
    "rms_velocity_mm_s": 2.1,
    "machine_group": "group2"
}

Output: JSON with classified faults and ISO severity.
"""

import json
import sys
import math


def classify(data: dict) -> dict:
    shaft = data["shaft_freq_hz"]
    peaks = {round(p["frequency_hz"], 1): p["amplitude"] for p in data["spectrum_peaks"]}
    kurtosis = data.get("kurtosis", 3.0)
    crest = data.get("crest_factor", 3.0)
    rms_vel = data.get("rms_velocity_mm_s", 0)
    group = data.get("machine_group", "group2")

    tolerance = shaft * 0.03  # 3% tolerance

    def amp_near(target):
        for f, a in peaks.items():
            if abs(f - target) <= tolerance:
                return a
        return 0.0

    a1x = amp_near(shaft)
    a2x = amp_near(2 * shaft)
    a3x = amp_near(3 * shaft)
    a05x = amp_near(0.5 * shaft)

    faults = []

    # Unbalance
    if a1x > 0 and (a2x == 0 or a1x / max(a2x, 1e-12) > 2):
        conf = "high" if (a2x == 0 or a1x / max(a2x, 1e-12) > 3) else "medium"
        faults.append({
            "type": "unbalance",
            "confidence": conf,
            "evidence": f"1x={a1x:.4f}, 2x={a2x:.4f}, ratio={a1x / max(a2x, 1e-12):.1f}",
        })

    # Misalignment
    if a2x > 0 and a1x > 0 and a2x / a1x > 0.5:
        conf = "high" if a2x > a1x else "medium"
        faults.append({
            "type": "misalignment",
            "confidence": conf,
            "evidence": f"2x={a2x:.4f}, 1x={a1x:.4f}, 2x/1x ratio={a2x / a1x:.2f}",
        })

    # Looseness
    if a05x > 0.001 or (a1x > 0 and a2x > 0 and a3x > 0):
        faults.append({
            "type": "mechanical_looseness",
            "confidence": "medium",
            "evidence": f"0.5x={a05x:.4f}, 1x={a1x:.4f}, 2x={a2x:.4f}, 3x={a3x:.4f}",
        })

    # Impulsive
    if kurtosis > 4.0 or crest > 5.0:
        faults.append({
            "type": "impulsive_signal",
            "confidence": "medium",
            "evidence": f"kurtosis={kurtosis:.2f}, crest_factor={crest:.2f}",
        })

    if not faults:
        faults.append({"type": "healthy", "confidence": "medium", "evidence": "No fault patterns found"})

    # ISO 10816
    thresholds = {
        "group1": (2.8, 7.1, 18.0),
        "group2": (1.4, 2.8, 7.1),
        "group3": (3.5, 9.0, 22.4),
        "group4": (0.71, 1.8, 4.5),
    }
    t = thresholds.get(group, thresholds["group2"])
    if rms_vel <= t[0]:
        zone = "A"
    elif rms_vel <= t[1]:
        zone = "B"
    elif rms_vel <= t[2]:
        zone = "C"
    else:
        zone = "D"

    return {
        "faults": faults,
        "iso_10816": {"zone": zone, "rms_velocity_mm_s": rms_vel, "group": group},
    }


if __name__ == "__main__":
    data = json.load(sys.stdin)
    print(json.dumps(classify(data), indent=2))
