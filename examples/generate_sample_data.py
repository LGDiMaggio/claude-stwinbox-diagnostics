"""
generate_sample_data.py — Create synthetic vibration data for testing.

Generates JSON files with realistic vibration signals containing known fault
signatures, so the analysis pipeline can be verified without actual hardware.

Usage:
    python generate_sample_data.py

Outputs:
    examples/sample_data/healthy_pump.json
    examples/sample_data/unbalance_motor.json
    examples/sample_data/bearing_fault_outer.json
"""

import json
import os
import numpy as np


def generate_signal(
    duration: float,
    fs: float,
    components: list[dict],
    noise_level: float = 0.01,
    seed: int = 42,
) -> dict:
    """
    Generate a synthetic vibration signal.
    
    Args:
        duration: Signal duration in seconds.
        fs: Sampling frequency in Hz.
        components: List of dicts with 'frequency', 'amplitude', and optional 'phase'.
        noise_level: RMS noise level.
        seed: Random seed for reproducibility.
    """
    rng = np.random.default_rng(seed)
    n = int(duration * fs)
    t = np.arange(n) / fs
    signal = np.zeros(n)
    
    for comp in components:
        f = comp["frequency"]
        a = comp["amplitude"]
        phi = comp.get("phase", 0.0)
        signal += a * np.sin(2 * np.pi * f * t + phi)
    
    signal += rng.normal(0, noise_level, n)
    
    return {
        "signal": signal.tolist(),
        "sample_rate_hz": fs,
        "duration_s": duration,
        "n_samples": n,
        "components": components,
    }


def add_bearing_impulses(
    signal: np.ndarray,
    fs: float,
    fault_freq: float,
    resonance_freq: float = 3000.0,
    amplitude: float = 0.1,
    damping: float = 500.0,
    seed: int = 123,
) -> np.ndarray:
    """Add modulated impulse train simulating a bearing defect."""
    rng = np.random.default_rng(seed)
    n = len(signal)
    t = np.arange(n) / fs
    duration = n / fs
    
    # Generate impulse at each fault period
    period = 1.0 / fault_freq
    impulse_times = np.arange(0, duration, period)
    
    out = signal.copy()
    for t0 in impulse_times:
        # Damped sinusoid at resonance frequency
        mask = t >= t0
        dt = t[mask] - t0
        impulse = amplitude * np.exp(-damping * dt) * np.sin(2 * np.pi * resonance_freq * dt)
        # Add some amplitude jitter
        impulse *= (1.0 + 0.1 * rng.normal())
        out[mask] += impulse
    
    return out


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    os.makedirs(out_dir, exist_ok=True)
    
    shaft_rpm = 1470.0
    shaft_freq = shaft_rpm / 60.0  # 24.5 Hz
    fs = 26667.0  # IIS3DWB sample rate
    duration = 2.0  # seconds
    
    # --- 1. Healthy pump ---
    healthy = generate_signal(
        duration, fs,
        components=[
            {"frequency": shaft_freq, "amplitude": 0.05, "phase": 0},
            {"frequency": 2 * shaft_freq, "amplitude": 0.01, "phase": 0.5},
            {"frequency": 3 * shaft_freq, "amplitude": 0.005, "phase": 1.0},
        ],
        noise_level=0.008,
        seed=42,
    )
    healthy["metadata"] = {
        "description": "Healthy centrifugal pump — normal vibration signature",
        "machine": "Centrifugal pump",
        "rpm": shaft_rpm,
        "sensor": "IIS3DWB",
        "axis": "radial_horizontal",
        "units": "g",
        "expected_diagnosis": "healthy",
    }
    with open(os.path.join(out_dir, "healthy_pump.json"), "w") as f:
        json.dump(healthy, f, indent=2)
    print(f"Created healthy_pump.json ({healthy['n_samples']} samples)")

    # --- 2. Motor with unbalance ---
    unbalance = generate_signal(
        duration, fs,
        components=[
            {"frequency": shaft_freq, "amplitude": 0.35, "phase": 0},       # Dominant 1×
            {"frequency": 2 * shaft_freq, "amplitude": 0.04, "phase": 0.3}, # Low 2×
            {"frequency": 3 * shaft_freq, "amplitude": 0.01, "phase": 0.8},
        ],
        noise_level=0.015,
        seed=43,
    )
    unbalance["metadata"] = {
        "description": "Electric motor with significant rotor unbalance",
        "machine": "3-phase induction motor, 22 kW",
        "rpm": shaft_rpm,
        "sensor": "IIS3DWB",
        "axis": "radial_horizontal",
        "units": "g",
        "expected_diagnosis": "unbalance",
    }
    with open(os.path.join(out_dir, "unbalance_motor.json"), "w") as f:
        json.dump(unbalance, f, indent=2)
    print(f"Created unbalance_motor.json ({unbalance['n_samples']} samples)")

    # --- 3. Bearing outer race fault ---
    # 6205 bearing at 1470 RPM: BPFO ≈ 88.2 Hz
    n_balls = 9
    ball_dia = 7.938
    pitch_dia = 38.5
    bpfo = shaft_freq * (n_balls / 2) * (1 - ball_dia / pitch_dia)  # ≈ 88.2 Hz

    bearing_base = generate_signal(
        duration, fs,
        components=[
            {"frequency": shaft_freq, "amplitude": 0.08, "phase": 0},
            {"frequency": 2 * shaft_freq, "amplitude": 0.03, "phase": 0.5},
        ],
        noise_level=0.02,
        seed=44,
    )
    
    sig_array = np.array(bearing_base["signal"])
    sig_with_fault = add_bearing_impulses(
        sig_array, fs,
        fault_freq=bpfo,
        resonance_freq=3200.0,
        amplitude=0.08,
        damping=400.0,
    )
    bearing_base["signal"] = sig_with_fault.tolist()
    bearing_base["metadata"] = {
        "description": "Pump with early outer-race bearing defect (6205 bearing)",
        "machine": "Centrifugal pump",
        "rpm": shaft_rpm,
        "bearing": "6205",
        "bpfo_hz": round(bpfo, 2),
        "sensor": "IIS3DWB",
        "axis": "radial_horizontal",
        "units": "g",
        "expected_diagnosis": "bearing_bpfo",
    }
    with open(os.path.join(out_dir, "bearing_fault_outer.json"), "w") as f:
        json.dump(bearing_base, f, indent=2)
    print(f"Created bearing_fault_outer.json ({bearing_base['n_samples']} samples)")
    
    print(f"\nAll sample data files saved to: {out_dir}")


if __name__ == "__main__":
    main()
