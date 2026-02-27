"""
Vibration Analysis MCP Server.

Exposes DSP and diagnostic tools via the Model Context Protocol so that
Claude can perform frequency analysis, envelope analysis, bearing-fault
detection, and ISO 10816 severity assessment on vibration data acquired
from the STWIN.box (or loaded from files).
"""

from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from .fft_analysis import compute_fft, compute_psd, compute_spectrogram, find_peaks_in_spectrum
from .envelope import envelope_spectrum, check_bearing_peaks
from .bearing_freqs import (
    compute_bearing_frequencies,
    get_bearing,
    list_bearings,
    COMMON_BEARINGS,
)
from .fault_detection import (
    assess_iso10816,
    extract_shaft_features,
    classify_faults,
    generate_diagnosis_summary,
)

mcp = FastMCP(
    "vibration-analysis",
    version="0.1.0",
    description=(
        "DSP & diagnostics toolkit for rotating-machinery vibration analysis. "
        "Provides FFT, PSD, envelope analysis, bearing fault-frequency calculation, "
        "and automated fault classification."
    ),
)


# ── FFT & spectral tools ─────────────────────────────────────────────────

@mcp.tool()
def compute_fft_spectrum(
    signal: list[float],
    sample_rate: float,
    window: str = "hann",
    n_fft: int | None = None,
) -> dict:
    """
    Compute the single-sided FFT amplitude spectrum of a vibration signal.
    
    Args:
        signal: Time-domain vibration samples (acceleration, velocity, etc.).
        sample_rate: Sampling frequency in Hz.
        window: Window function name ('hann', 'hamming', 'blackman', 'rectangular').
        n_fft: FFT length. Defaults to signal length.
    """
    import numpy as np
    result = compute_fft(np.array(signal), sample_rate, window=window, n_fft=n_fft)
    return {
        "frequencies_hz": result["frequencies"],
        "amplitudes": result["magnitudes"],
        "n_samples": len(signal),
        "sample_rate_hz": sample_rate,
        "window": window,
        "frequency_resolution_hz": result["frequencies"][1] if len(result["frequencies"]) > 1 else 0,
    }


@mcp.tool()
def compute_power_spectral_density(
    signal: list[float],
    sample_rate: float,
    segment_length: int | None = None,
    overlap_pct: float = 50.0,
) -> dict:
    """
    Compute the Power Spectral Density (Welch method).
    
    Args:
        signal: Time-domain vibration samples.
        sample_rate: Sampling frequency in Hz.
        segment_length: Welch segment length in samples (default: len/8).
        overlap_pct: Overlap percentage between segments.
    """
    import numpy as np
    result = compute_psd(
        np.array(signal), sample_rate,
        nperseg=segment_length,
        overlap_pct=overlap_pct,
    )
    return {
        "frequencies_hz": result["frequencies"],
        "psd_values": result["psd"],
        "units": "signal_unit²/Hz",
        "n_samples": len(signal),
    }


@mcp.tool()
def compute_spectrogram_stft(
    signal: list[float],
    sample_rate: float,
    segment_length: int = 256,
    overlap_pct: float = 75.0,
) -> dict:
    """
    Compute a Short-Time Fourier Transform spectrogram.
    Useful for analysing non-stationary signals (run-up/coast-down).
    
    Args:
        signal: Time-domain vibration samples.
        sample_rate: Sampling frequency in Hz.
        segment_length: Window length in samples.
        overlap_pct: Overlap percentage.
    """
    import numpy as np
    result = compute_spectrogram(
        np.array(signal), sample_rate,
        nperseg=segment_length,
        overlap_pct=overlap_pct,
    )
    return {
        "frequencies_hz": result["frequencies"],
        "time_s": result["times"],
        "spectrogram_db": result["spectrogram_db"],
        "sample_rate_hz": sample_rate,
    }


@mcp.tool()
def find_spectral_peaks(
    frequencies: list[float],
    amplitudes: list[float],
    min_height: float | None = None,
    min_distance_hz: float = 5.0,
    top_n: int = 10,
) -> dict:
    """
    Find dominant peaks in a frequency spectrum.
    
    Args:
        frequencies: Frequency axis in Hz.
        amplitudes: Spectrum amplitudes.
        min_height: Minimum peak amplitude (auto if None).
        min_distance_hz: Minimum distance between peaks in Hz.
        top_n: Return only the N highest peaks.
    """
    import numpy as np
    peaks = find_peaks_in_spectrum(
        np.array(frequencies),
        np.array(amplitudes),
        min_height=min_height,
        min_distance_hz=min_distance_hz,
        top_n=top_n,
    )
    return {
        "peaks": peaks,
        "count": len(peaks),
    }


# ── Envelope analysis tools ──────────────────────────────────────────────

@mcp.tool()
def compute_envelope_spectrum(
    signal: list[float],
    sample_rate: float,
    band_low_hz: float | None = None,
    band_high_hz: float | None = None,
) -> dict:
    """
    Compute the envelope spectrum for bearing fault detection.
    The signal is band-pass filtered, the Hilbert-transform envelope is
    extracted, and its FFT is computed to reveal bearing fault frequencies.
    
    Args:
        signal: Raw vibration time-domain samples.
        sample_rate: Sampling frequency in Hz.
        band_low_hz: Band-pass lower cutoff. Auto if None.
        band_high_hz: Band-pass upper cutoff. Auto if None.
    """
    result = envelope_spectrum(
        __import__("numpy").array(signal),
        sample_rate,
        band_low=band_low_hz,
        band_high=band_high_hz,
    )
    return {
        "frequencies_hz": result["frequencies"],
        "envelope_amplitudes": result["envelope_spectrum"],
        "filter_band_hz": list(result["filter_band"]),
        "n_samples": result["n_samples"],
    }


@mcp.tool()
def check_bearing_fault_peak(
    frequencies: list[float],
    amplitudes: list[float],
    target_frequency_hz: float,
    n_harmonics: int = 3,
    tolerance_pct: float = 3.0,
) -> dict:
    """
    Check whether a bearing fault frequency (and harmonics) is present
    in an envelope spectrum.
    
    Args:
        frequencies: Envelope spectrum frequency axis (Hz).
        amplitudes: Envelope spectrum magnitudes.
        target_frequency_hz: Expected fault frequency (BPFO, BPFI, etc.) in Hz.
        n_harmonics: Number of harmonics to check (1× through N×).
        tolerance_pct: Frequency matching tolerance in percent.
    """
    return check_bearing_peaks(
        frequencies, amplitudes,
        target_freq=target_frequency_hz,
        n_harmonics=n_harmonics,
        tolerance_pct=tolerance_pct,
    )


# ── Bearing frequency tools ──────────────────────────────────────────────

@mcp.tool()
def calculate_bearing_frequencies(
    rpm: float,
    n_balls: int,
    ball_diameter_mm: float,
    pitch_diameter_mm: float,
    contact_angle_deg: float = 0.0,
    bearing_name: str = "",
) -> dict:
    """
    Compute bearing characteristic frequencies (BPFO, BPFI, BSF, FTF)
    from bearing geometry and shaft RPM.
    
    Args:
        rpm: Shaft speed in revolutions per minute.
        n_balls: Number of rolling elements.
        ball_diameter_mm: Ball or roller diameter in mm.
        pitch_diameter_mm: Pitch (cage) diameter in mm.
        contact_angle_deg: Contact angle in degrees (0 for radial bearings).
        bearing_name: Optional bearing designation for labeling.
    """
    result = compute_bearing_frequencies(
        rpm, n_balls, ball_diameter_mm, pitch_diameter_mm,
        contact_angle_deg, bearing_name or "custom",
    )
    return result.to_dict()


@mcp.tool()
def lookup_bearing_and_compute(
    designation: str,
    rpm: float,
) -> dict:
    """
    Look up a common bearing by its designation (e.g., '6205', '6306', 'NU206')
    and compute its characteristic frequencies at the given RPM.
    
    Args:
        designation: Standard bearing designation string.
        rpm: Shaft speed in RPM.
    """
    bearing = get_bearing(designation)
    if bearing is None:
        return {
            "error": f"Bearing '{designation}' not found in database.",
            "available": [k for k in COMMON_BEARINGS],
        }
    result = compute_bearing_frequencies(
        rpm, bearing.n_balls, bearing.ball_dia, bearing.pitch_dia,
        bearing.contact_angle, bearing.name,
    )
    return result.to_dict()


@mcp.tool()
def list_known_bearings() -> dict:
    """
    List all bearings available in the built-in database
    with their geometric parameters.
    """
    return {"bearings": list_bearings()}


# ── Fault detection & diagnosis tools ────────────────────────────────────

@mcp.tool()
def assess_vibration_severity(
    rms_velocity_mm_s: float,
    machine_group: str = "group2",
) -> dict:
    """
    Classify vibration severity per ISO 10816.
    
    Machine groups:
        group1 – Large machines (>300 kW) on rigid foundations
        group2 – Medium machines (15–300 kW) on rigid foundations
        group3 – Large machines on flexible foundations
        group4 – Small machines (<15 kW)
    
    Args:
        rms_velocity_mm_s: Overall RMS velocity in mm/s (10–1000 Hz band).
        machine_group: ISO 10816 machine group identifier.
    """
    return assess_iso10816(rms_velocity_mm_s, machine_group)


@mcp.tool()
def diagnose_vibration(
    signal: list[float],
    sample_rate: float,
    rpm: float,
    bearing_designation: str | None = None,
    machine_group: str = "group2",
    machine_description: str = "",
) -> dict:
    """
    Full automated vibration diagnosis pipeline.
    
    1. Compute FFT and extract shaft-frequency features
    2. Optionally perform envelope analysis for bearing faults
    3. Classify faults (unbalance, misalignment, looseness, bearing)
    4. Assess ISO 10816 severity
    5. Generate human-readable report
    
    Args:
        signal: Vibration time-domain signal (acceleration in g or m/s²).
        sample_rate: Sampling frequency in Hz.
        rpm: Shaft speed in RPM.
        bearing_designation: Optional bearing code (e.g., '6205') for envelope analysis.
        machine_group: ISO 10816 group ('group1'..'group4').
        machine_description: Free text describing the machine for the report.
    """
    import numpy as np
    
    sig = np.array(signal)
    shaft_freq = rpm / 60.0
    
    # Step 1: FFT
    fft_result = compute_fft(sig, sample_rate)
    freqs = np.array(fft_result["frequencies"])
    mags = np.array(fft_result["magnitudes"])
    
    # Step 2: Shaft features
    features = extract_shaft_features(freqs, mags, shaft_freq, time_signal=sig)
    
    # Step 3: Envelope analysis for bearings (if bearing info provided)
    bearing_results = None
    if bearing_designation:
        bearing = get_bearing(bearing_designation)
        if bearing:
            bf = compute_bearing_frequencies(
                rpm, bearing.n_balls, bearing.ball_dia, bearing.pitch_dia,
                bearing.contact_angle, bearing.name,
            )
            env = envelope_spectrum(sig, sample_rate)
            env_freqs = np.array(env["frequencies"])
            env_mags = np.array(env["envelope_spectrum"])
            bearing_results = {}
            for key, freq_val in [
                ("bpfo", bf.bpfo), ("bpfi", bf.bpfi),
                ("bsf", bf.bsf), ("ftf", bf.ftf),
            ]:
                bearing_results[key] = check_bearing_peaks(
                    env_freqs, env_mags, freq_val
                )
    
    # Step 4: Classify
    diagnoses = classify_faults(features, bearing_results)
    
    # Step 5: ISO 10816 (approximate RMS velocity from acceleration)
    # Very rough: integrate accel -> velocity via division by 2*pi*f
    # Here we just report the overall RMS of the signal as-is
    rms_overall = float(np.sqrt(np.mean(sig**2)))
    iso = assess_iso10816(rms_overall, machine_group)
    
    # Step 6: Report
    report = generate_diagnosis_summary(diagnoses, iso, machine_description)
    
    return {
        "diagnoses": [d.to_dict() for d in diagnoses],
        "iso_10816": iso,
        "shaft_features": {
            "shaft_freq_hz": features.f_shaft,
            "amp_1x": round(features.amp_1x, 6),
            "amp_2x": round(features.amp_2x, 6),
            "amp_3x": round(features.amp_3x, 6),
            "amp_half_x": round(features.amp_half_x, 6),
            "kurtosis": round(features.kurtosis, 2),
            "crest_factor": round(features.crest_factor, 2),
        },
        "bearing_analysis": (
            {k: v for k, v in bearing_results.items()} if bearing_results else None
        ),
        "report_markdown": report,
    }


# ── Resource: analysis capabilities ──────────────────────────────────────

@mcp.resource("vibration-analysis://capabilities")
def analysis_capabilities() -> str:
    """List all analysis capabilities of this server."""
    return json.dumps({
        "spectral_analysis": [
            "FFT (amplitude spectrum)",
            "Power Spectral Density (Welch)",
            "Spectrogram (STFT)",
            "Peak detection",
        ],
        "envelope_analysis": [
            "Band-pass filtering (Butterworth)",
            "Hilbert-transform envelope",
            "Envelope spectrum",
            "Bearing fault-frequency peak matching",
        ],
        "bearing_frequencies": [
            "BPFO (Ball Pass Frequency Outer)",
            "BPFI (Ball Pass Frequency Inner)",
            "BSF (Ball Spin Frequency)",
            "FTF (Fundamental Train / Cage Frequency)",
            "Built-in database of common bearings",
        ],
        "fault_detection": [
            "Unbalance (1× dominant)",
            "Misalignment (2×, 3×)",
            "Mechanical looseness (sub-harmonics)",
            "Bearing defects (envelope + fault frequencies)",
            "Impulsive content (kurtosis, crest factor)",
        ],
        "standards": [
            "ISO 10816 vibration severity (Groups 1–4)",
        ],
    }, indent=2)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
