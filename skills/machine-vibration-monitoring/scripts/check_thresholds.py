"""
check_thresholds.py — Compare current vibration measurement against baseline.

Usage by Claude:
    Run this script with current and baseline FFT peak data to identify
    significant changes in the vibration signature.
"""

import json
import sys


def compare_baselines(current_peaks: list[dict], baseline_peaks: list[dict],
                      amplitude_threshold_db: float = 6.0,
                      new_peak_threshold: float = 0.001) -> dict:
    """
    Compare current spectral peaks against a stored baseline.
    
    Args:
        current_peaks: List of {frequency_hz, amplitude} dicts from current measurement.
        baseline_peaks: List of {frequency_hz, amplitude} dicts from baseline.
        amplitude_threshold_db: Minimum amplitude change in dB to flag (default 6 dB = 2×).
        new_peak_threshold: Minimum amplitude to consider a peak significant.
        
    Returns:
        dict with changed_peaks, new_peaks, disappeared_peaks, summary.
    """
    import math
    
    tolerance_hz = 2.0  # How close frequencies must be to be "same" peak
    
    changed = []
    new_peaks = []
    disappeared = []
    
    # Match current peaks to baseline
    baseline_matched = set()
    for cp in current_peaks:
        cf = cp["frequency_hz"]
        ca = cp["amplitude"]
        
        # Find closest baseline peak
        best_match = None
        best_dist = float("inf")
        for i, bp in enumerate(baseline_peaks):
            dist = abs(bp["frequency_hz"] - cf)
            if dist < tolerance_hz and dist < best_dist:
                best_match = (i, bp)
                best_dist = dist
        
        if best_match is not None:
            idx, bp = best_match
            baseline_matched.add(idx)
            ba = bp["amplitude"]
            if ba > 0:
                change_db = 20 * math.log10(ca / ba) if ca > 0 else -100
            else:
                change_db = 100 if ca > 0 else 0
            
            if abs(change_db) >= amplitude_threshold_db:
                changed.append({
                    "frequency_hz": cf,
                    "baseline_amplitude": ba,
                    "current_amplitude": ca,
                    "change_db": round(change_db, 1),
                    "status": "increased" if change_db > 0 else "decreased",
                })
        else:
            if ca >= new_peak_threshold:
                new_peaks.append({
                    "frequency_hz": cf,
                    "amplitude": ca,
                    "status": "new_peak",
                })
    
    # Peaks in baseline that disappeared
    for i, bp in enumerate(baseline_peaks):
        if i not in baseline_matched and bp["amplitude"] >= new_peak_threshold:
            disappeared.append({
                "frequency_hz": bp["frequency_hz"],
                "amplitude": bp["amplitude"],
                "status": "disappeared",
            })
    
    return {
        "changed_peaks": changed,
        "new_peaks": new_peaks,
        "disappeared_peaks": disappeared,
        "summary": {
            "total_changes": len(changed) + len(new_peaks) + len(disappeared),
            "increased": sum(1 for c in changed if c["status"] == "increased"),
            "decreased": sum(1 for c in changed if c["status"] == "decreased"),
            "new": len(new_peaks),
            "disappeared": len(disappeared),
            "needs_attention": len(changed) > 0 or len(new_peaks) > 0,
        },
    }


if __name__ == "__main__":
    # Read from stdin for Claude scripting
    data = json.load(sys.stdin)
    result = compare_baselines(
        data["current_peaks"],
        data["baseline_peaks"],
        data.get("threshold_db", 6.0),
    )
    print(json.dumps(result, indent=2))
