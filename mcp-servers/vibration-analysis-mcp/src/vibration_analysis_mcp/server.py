"""
Vibration Analysis MCP Server.

Exposes DSP and diagnostic tools via the Model Context Protocol so that
Claude can perform frequency analysis, envelope analysis, bearing-fault
detection, and ISO 10816 severity assessment on vibration data acquired
from the STWIN.box (or loaded from files).
"""

from __future__ import annotations

import json
from typing import Optional

import numpy as np
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
from .data_store import store

mcp = FastMCP(
    "vibration-analysis",
    instructions=(
        "DSP & diagnostics toolkit for rotating-machinery vibration analysis. "
        "Provides FFT, PSD, envelope analysis, bearing fault-frequency calculation, "
        "and automated fault classification.\n\n"
        "SIGNAL HANDLING — Vibration signals are stored server-side to avoid "
        "flooding the conversation context. Use load_signal to load a .dat/.csv "
        "file into the store, then pass the returned data_id to any analysis tool. "
        "Tools also accept a raw signal list for small ad-hoc analyses.\n\n"
        "All spectral tools return compact summaries (top peaks + statistics), "
        "not full-length arrays."
    ),
)


# ── Helpers ───────────────────────────────────────────────────────────────

def _resolve_signal(
    data_id: str | None,
    signal: list[float] | None,
    sample_rate: float | None,
    channel: str = "X",
) -> tuple[np.ndarray, float]:
    """Return (1-D numpy signal, sample_rate) from either a data_id or raw list."""
    if data_id is not None:
        entry = store.get(data_id)
        if entry is None:
            available = store.list_ids()
            raise ValueError(
                f"data_id '{data_id}' not found in store. "
                f"Available: {available or '(empty — use load_signal first)'}."
            )
        sig = entry.signal
        sr = entry.sample_rate
        if sig.ndim > 1:
            ch_map = {"X": 0, "Y": 1, "Z": 2}
            idx = ch_map.get(channel.upper(), int(channel) if channel.isdigit() else 0)
            idx = min(idx, sig.shape[1] - 1)
            sig = sig[:, idx]
        return sig, sr
    if signal is not None:
        if sample_rate is None or sample_rate <= 0:
            raise ValueError("sample_rate is required when passing a raw signal list.")
        return np.asarray(signal, dtype=np.float64), float(sample_rate)
    raise ValueError("Provide either data_id (preferred) or signal + sample_rate.")


def _compact_spectrum(freqs: np.ndarray, mags: np.ndarray, top_n: int = 20) -> dict:
    """Summarise a spectrum: top N peaks + global stats. No full arrays."""
    # Top N peaks by amplitude
    order = np.argsort(mags)[::-1]
    n = min(top_n, len(order))
    top_idx = np.sort(order[:n])  # sort back by frequency
    peaks = [
        {"freq_hz": round(float(freqs[i]), 3), "amplitude": round(float(mags[i]), 6)}
        for i in top_idx
    ]
    return {
        "top_peaks": peaks,
        "max_amplitude": round(float(np.max(mags)), 6),
        "max_amplitude_freq_hz": round(float(freqs[np.argmax(mags)]), 3),
        "rms_spectral": round(float(np.sqrt(np.mean(mags**2))), 6),
        "total_bins": len(freqs),
        "freq_range_hz": [round(float(freqs[0]), 3), round(float(freqs[-1]), 3)],
    }


# ── Signal store tools ────────────────────────────────────────────────────

@mcp.tool()
def load_signal(
    file_path: str,
    sample_rate: float,
    sensor_name: str = "iis3dwb",
    axes: int = 3,
    data_id: str | None = None,
) -> dict:
    """
    Load a vibration data file (.csv or .dat) into the server-side store.
    Returns a data_id and compact summary — the raw signal never enters the
    conversation context.

    Args:
        file_path: Absolute path to the data file.
        sample_rate: Sampling frequency in Hz (e.g., 26667 for IIS3DWB).
        sensor_name: Sensor that produced the data ('iis3dwb', 'ism330dhcx', …).
        axes: Number of axes in the data (3 for accelerometer, 1 for mic).
        data_id: Optional human-readable ID. Auto-generated if omitted.
    """
    try:
        did, summary = store.load_from_file(
            file_path, sample_rate, sensor_name, axes, data_id,
        )
        return {"data_id": did, **summary}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def list_stored_signals() -> dict:
    """
    List all signals currently held in the server-side store, with their
    statistics (RMS, peak, crest factor, kurtosis, duration, etc.).
    """
    entries = store.list_entries()
    return {"count": len(entries), "signals": entries}


# ── FFT & spectral tools ─────────────────────────────────────────────────

@mcp.tool()
def compute_fft_spectrum(
    data_id: str | None = None,
    signal: list[float] | None = None,
    sample_rate: float | None = None,
    channel: str = "X",
    window: str = "hann",
    n_fft: int | None = None,
    top_n: int = 20,
) -> dict:
    """
    Compute the single-sided FFT amplitude spectrum of a vibration signal.
    Returns a compact summary (top N peaks + statistics), not the full array.

    Provide **data_id** (preferred) to reference a signal in the store,
    or **signal** + **sample_rate** for a small ad-hoc list.

    Args:
        data_id: Reference to a stored signal (from load_signal).
        signal: Time-domain vibration samples (use data_id instead for large signals).
        sample_rate: Sampling frequency in Hz (required if signal is given).
        channel: Axis to analyse when the stored signal is multi-axis ('X','Y','Z').
        window: Window function ('hann', 'hamming', 'blackman', 'rectangular').
        n_fft: FFT length. Defaults to signal length.
        top_n: Number of highest peaks to include in the summary.
    """
    try:
        sig, sr = _resolve_signal(data_id, signal, sample_rate, channel)
    except ValueError as e:
        return {"error": str(e)}
    result = compute_fft(sig, sr, window=window, n_fft=n_fft)
    freqs = np.asarray(result["frequencies"])
    mags = np.asarray(result["magnitude"])
    summary = _compact_spectrum(freqs, mags, top_n=top_n)
    summary.update({
        "n_samples": len(sig),
        "sample_rate_hz": sr,
        "window": window,
        "frequency_resolution_hz": round(float(freqs[1]), 4) if len(freqs) > 1 else 0,
    })
    if data_id:
        summary["data_id"] = data_id
        summary["channel"] = channel
    return summary


@mcp.tool()
def compute_power_spectral_density(
    data_id: str | None = None,
    signal: list[float] | None = None,
    sample_rate: float | None = None,
    channel: str = "X",
    segment_length: int | None = None,
    overlap_pct: float = 50.0,
    top_n: int = 20,
) -> dict:
    """
    Compute the Power Spectral Density (Welch method).
    Returns a compact summary (top N peaks + stats), not the full array.

    Args:
        data_id: Reference to a stored signal (from load_signal).
        signal: Time-domain vibration samples (use data_id for large signals).
        sample_rate: Sampling frequency in Hz (required if signal is given).
        channel: Axis to analyse ('X','Y','Z').
        segment_length: Welch segment length in samples (default: len/8).
        overlap_pct: Overlap percentage between segments.
        top_n: Number of highest peaks to include.
    """
    try:
        sig, sr = _resolve_signal(data_id, signal, sample_rate, channel)
    except ValueError as e:
        return {"error": str(e)}
    nperseg = segment_length or max(256, len(sig) // 8)
    noverlap = int(nperseg * overlap_pct / 100.0)
    result = compute_psd(sig, sr, nperseg=nperseg, noverlap=noverlap)
    freqs = np.asarray(result["frequencies"])
    psd = np.asarray(result["psd"])
    summary = _compact_spectrum(freqs, psd, top_n=top_n)
    summary.update({
        "units": "signal_unit²/Hz",
        "n_samples": len(sig),
        "sample_rate_hz": sr,
    })
    if data_id:
        summary["data_id"] = data_id
        summary["channel"] = channel
    return summary


@mcp.tool()
def compute_spectrogram_stft(
    data_id: str | None = None,
    signal: list[float] | None = None,
    sample_rate: float | None = None,
    channel: str = "X",
    segment_length: int = 256,
    overlap_pct: float = 75.0,
) -> dict:
    """
    Compute a Short-Time Fourier Transform spectrogram.
    Useful for analysing non-stationary signals (run-up / coast-down).

    Returns a compact summary (dominant frequency per time segment),
    not the full 2-D array.

    Args:
        data_id: Reference to a stored signal (from load_signal).
        signal: Time-domain vibration samples (use data_id for large signals).
        sample_rate: Sampling frequency in Hz (required if signal is given).
        channel: Axis to analyse ('X','Y','Z').
        segment_length: Window length in samples.
        overlap_pct: Overlap percentage.
    """
    try:
        sig, sr = _resolve_signal(data_id, signal, sample_rate, channel)
    except ValueError as e:
        return {"error": str(e)}
    noverlap = int(segment_length * overlap_pct / 100.0)
    result = compute_spectrogram(sig, sr, nperseg=segment_length, noverlap=noverlap)
    spec_db = np.asarray(result["spectrogram_db"])
    freqs = np.asarray(result["frequencies"])
    times = np.asarray(result["times"])
    # Dominant frequency per time slice
    dom_idx = np.argmax(spec_db, axis=0)
    slices = []
    step = max(1, len(times) // 20)  # up to 20 representative slices
    for i in range(0, len(times), step):
        slices.append({
            "time_s": round(float(times[i]), 4),
            "dominant_freq_hz": round(float(freqs[dom_idx[i]]), 2),
            "peak_power_db": round(float(spec_db[dom_idx[i], i]), 2),
        })
    return {
        "time_range_s": [round(float(times[0]), 4), round(float(times[-1]), 4)],
        "freq_range_hz": [round(float(freqs[0]), 2), round(float(freqs[-1]), 2)],
        "n_time_segments": len(times),
        "n_freq_bins": len(freqs),
        "representative_slices": slices,
        "sample_rate_hz": sr,
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
    kwargs = {"min_distance_hz": min_distance_hz, "num_peaks": top_n}
    if min_height is not None:
        # Convert linear min_height to dB for the internal threshold
        kwargs["threshold_db"] = float(20 * np.log10(max(min_height, 1e-12)))
    peaks = find_peaks_in_spectrum(
        np.array(frequencies),
        np.array(amplitudes),
        **kwargs,
    )
    return {
        "peaks": peaks,
        "count": len(peaks),
    }


# ── Envelope analysis tools ──────────────────────────────────────────────

@mcp.tool()
def compute_envelope_spectrum(
    data_id: str | None = None,
    signal: list[float] | None = None,
    sample_rate: float | None = None,
    channel: str = "X",
    band_low_hz: float | None = None,
    band_high_hz: float | None = None,
    top_n: int = 20,
) -> dict:
    """
    Compute the envelope spectrum for bearing fault detection.
    The signal is band-pass filtered, the Hilbert-transform envelope is
    extracted, and its FFT is computed to reveal bearing fault frequencies.

    Returns a compact summary (top N peaks + stats), not the full array.

    Args:
        data_id: Reference to a stored signal (from load_signal).
        signal: Raw vibration time-domain samples (use data_id for large signals).
        sample_rate: Sampling frequency in Hz (required if signal is given).
        channel: Axis to analyse ('X','Y','Z').
        band_low_hz: Band-pass lower cutoff. Auto if None.
        band_high_hz: Band-pass upper cutoff. Auto if None.
        top_n: Number of highest peaks to include.
    """
    try:
        sig, sr = _resolve_signal(data_id, signal, sample_rate, channel)
    except ValueError as e:
        return {"error": str(e)}
    result = envelope_spectrum(sig, sr, band_low=band_low_hz, band_high=band_high_hz)
    freqs = np.asarray(result["frequencies"])
    env_mags = np.asarray(result["envelope_spectrum"])
    summary = _compact_spectrum(freqs, env_mags, top_n=top_n)
    summary.update({
        "filter_band_hz": list(result["filter_band"]),
        "n_samples": result["n_samples"],
        "sample_rate_hz": sr,
    })
    if data_id:
        summary["data_id"] = data_id
        summary["channel"] = channel
    return summary


@mcp.tool()
def check_bearing_fault_peak(
    target_frequency_hz: float,
    data_id: str | None = None,
    channel: str = "X",
    frequencies: list[float] | None = None,
    amplitudes: list[float] | None = None,
    sample_rate: float | None = None,
    n_harmonics: int = 3,
    tolerance_pct: float = 3.0,
    band_low_hz: float | None = None,
    band_high_hz: float | None = None,
) -> dict:
    """
    Check whether a bearing fault frequency (and harmonics) is present.

    Two modes:
    - **data_id** (preferred): provide a stored raw signal; envelope spectrum
      is computed internally.
    - **frequencies + amplitudes**: provide a pre-computed envelope spectrum.

    Args:
        target_frequency_hz: Expected fault frequency (BPFO, BPFI, etc.) in Hz.
        data_id: Reference to a stored raw signal.
        channel: Axis to analyse when using data_id ('X','Y','Z').
        frequencies: Pre-computed envelope spectrum frequency axis (Hz).
        amplitudes: Pre-computed envelope spectrum magnitudes.
        sample_rate: Required only when passing frequencies/amplitudes directly.
        n_harmonics: Number of harmonics to check (1× through N×).
        tolerance_pct: Frequency matching tolerance in percent.
        band_low_hz: Envelope band-pass lower cutoff (only with data_id).
        band_high_hz: Envelope band-pass upper cutoff (only with data_id).
    """
    if data_id is not None:
        try:
            sig, sr = _resolve_signal(data_id, None, None, channel)
        except ValueError as e:
            return {"error": str(e)}
        env = envelope_spectrum(sig, sr, band_low=band_low_hz, band_high=band_high_hz)
        freqs_arr = np.asarray(env["frequencies"])
        amps_arr = np.asarray(env["envelope_spectrum"])
    elif frequencies is not None and amplitudes is not None:
        freqs_arr = np.asarray(frequencies)
        amps_arr = np.asarray(amplitudes)
    else:
        return {"error": "Provide data_id or (frequencies + amplitudes)."}

    return check_bearing_peaks(
        freqs_arr, amps_arr,
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


@mcp.tool()
def check_bearing_faults_direct(
    data_id: str | None = None,
    channel: str = "X",
    frequencies: list[float] | None = None,
    amplitudes: list[float] | None = None,
    rpm: float | None = None,
    bpfo_hz: float | None = None,
    bpfi_hz: float | None = None,
    bsf_hz: float | None = None,
    ftf_hz: float | None = None,
    bpfo_order: float | None = None,
    bpfi_order: float | None = None,
    bsf_order: float | None = None,
    ftf_order: float | None = None,
    n_harmonics: int = 3,
    tolerance_pct: float = 3.0,
    band_low_hz: float | None = None,
    band_high_hz: float | None = None,
) -> dict:
    """
    Check for bearing faults using known fault frequencies provided directly
    by the user — no geometry or database lookup needed.

    Two modes for the spectrum input:
    - **data_id** (preferred): stored raw signal → envelope computed internally.
    - **frequencies + amplitudes**: pre-computed envelope spectrum.

    Fault frequencies can be supplied as:
    - **Absolute (Hz)**: bpfo_hz, bpfi_hz, bsf_hz, ftf_hz
    - **Orders (× shaft speed)**: bpfo_order … ftf_order (requires `rpm`).
      Hz takes priority when both are given.

    Args:
        data_id: Reference to a stored raw signal.
        channel: Axis to analyse when using data_id ('X','Y','Z').
        frequencies: Pre-computed envelope spectrum frequency axis (Hz).
        amplitudes: Pre-computed envelope spectrum magnitudes.
        rpm: Shaft speed in RPM (required when using _order parameters).
        bpfo_hz: Ball Pass Frequency Outer race in Hz.
        bpfi_hz: Ball Pass Frequency Inner race in Hz.
        bsf_hz: Ball Spin Frequency in Hz.
        ftf_hz: Fundamental Train (cage) Frequency in Hz.
        bpfo_order: BPFO as a multiple of shaft speed (e.g., 3.56×).
        bpfi_order: BPFI as a multiple of shaft speed (e.g., 5.44×).
        bsf_order: BSF as a multiple of shaft speed (e.g., 2.32×).
        ftf_order: FTF as a multiple of shaft speed (e.g., 0.40×).
        n_harmonics: Number of harmonics to check (1× through N×).
        tolerance_pct: Frequency matching tolerance in percent.
        band_low_hz: Envelope band-pass lower cutoff (only with data_id).
        band_high_hz: Envelope band-pass upper cutoff (only with data_id).
    """
    # Resolve envelope spectrum
    if data_id is not None:
        try:
            sig, sr = _resolve_signal(data_id, None, None, channel)
        except ValueError as e:
            return {"error": str(e)}
        env = envelope_spectrum(sig, sr, band_low=band_low_hz, band_high=band_high_hz)
        env_freqs = np.asarray(env["frequencies"])
        env_amps = np.asarray(env["envelope_spectrum"])
    elif frequencies is not None and amplitudes is not None:
        env_freqs = np.asarray(frequencies)
        env_amps = np.asarray(amplitudes)
    else:
        return {"error": "Provide data_id (raw signal) or (frequencies + amplitudes) of an envelope spectrum."}

    # Resolve orders -> Hz
    shaft_freq = (rpm / 60.0) if rpm and rpm > 0 else None
    resolved: dict[str, float] = {}
    for key, hz_val, order_val in [
        ("bpfo", bpfo_hz, bpfo_order),
        ("bpfi", bpfi_hz, bpfi_order),
        ("bsf", bsf_hz, bsf_order),
        ("ftf", ftf_hz, ftf_order),
    ]:
        if hz_val is not None and hz_val > 0:
            resolved[key] = hz_val
        elif order_val is not None and order_val > 0:
            if shaft_freq is None:
                return {"error": f"{key}_order was provided but rpm is missing. Supply rpm to convert orders to Hz."}
            resolved[key] = order_val * shaft_freq

    if not resolved:
        return {"error": "No fault frequencies provided. Supply at least one of bpfo_hz/bpfo_order, bpfi_hz/bpfi_order, bsf_hz/bsf_order, ftf_hz/ftf_order."}

    results: dict = {}
    for key, freq_val in resolved.items():
        results[key] = check_bearing_peaks(
            env_freqs, env_amps,
            target_freq=freq_val,
            n_harmonics=n_harmonics,
            tolerance_pct=tolerance_pct,
        )
        results[key]["target_frequency_hz"] = round(freq_val, 3)
    if shaft_freq:
        results["shaft_frequency_hz"] = round(shaft_freq, 3)
        results["input_mode"] = "orders converted to Hz" if any(
            o is not None and o > 0 for o in [bpfo_order, bpfi_order, bsf_order, ftf_order]
        ) else "direct Hz"
    return results


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
    rpm: float,
    data_id: str | None = None,
    channel: str = "X",
    signal: list[float] | None = None,
    sample_rate: float | None = None,
    bearing_designation: str | None = None,
    bearing_n_balls: int | None = None,
    bearing_ball_dia_mm: float | None = None,
    bearing_pitch_dia_mm: float | None = None,
    bearing_contact_angle_deg: float = 0.0,
    bpfo_hz: float | None = None,
    bpfi_hz: float | None = None,
    bsf_hz: float | None = None,
    ftf_hz: float | None = None,
    bpfo_order: float | None = None,
    bpfi_order: float | None = None,
    bsf_order: float | None = None,
    ftf_order: float | None = None,
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

    Signal input: provide **data_id** (preferred) to reference a signal in the
    store, or **signal** + **sample_rate** for a small ad-hoc list.

    Bearing information can be provided in four ways (in priority order):
    a) Direct fault frequencies in Hz: bpfo_hz, bpfi_hz, bsf_hz, ftf_hz
    b) Fault frequency orders (× shaft speed): bpfo_order … ftf_order
    c) Custom geometry: bearing_n_balls, bearing_ball_dia_mm, bearing_pitch_dia_mm
    d) Database lookup: bearing_designation (e.g., '6205', 'NU206')

    Args:
        rpm: Shaft speed in RPM.
        data_id: Reference to a stored signal (from load_signal).
        channel: Axis to analyse when using data_id ('X','Y','Z').
        signal: Vibration samples (use data_id for large signals).
        sample_rate: Sampling frequency in Hz (required if signal is given).
        bearing_designation: Bearing code from built-in database.
        bearing_n_balls: Number of rolling elements (custom geometry).
        bearing_ball_dia_mm: Ball diameter in mm (custom geometry).
        bearing_pitch_dia_mm: Pitch diameter in mm (custom geometry).
        bearing_contact_angle_deg: Contact angle in degrees (default 0).
        bpfo_hz: Known BPFO in Hz.
        bpfi_hz: Known BPFI in Hz.
        bsf_hz: Known BSF in Hz.
        ftf_hz: Known FTF in Hz.
        bpfo_order: BPFO as multiple of shaft speed (e.g., 3.56×).
        bpfi_order: BPFI as multiple of shaft speed (e.g., 5.44×).
        bsf_order: BSF as multiple of shaft speed (e.g., 2.32×).
        ftf_order: FTF as multiple of shaft speed (e.g., 0.40×).
        machine_group: ISO 10816 group ('group1'..'group4').
        machine_description: Free text describing the machine for the report.
    """
    try:
        sig, sr = _resolve_signal(data_id, signal, sample_rate, channel)
    except ValueError as e:
        return {"error": str(e)}

    shaft_freq = rpm / 60.0
    
    # Step 1: FFT
    fft_result = compute_fft(sig, sr)
    freqs = np.array(fft_result["frequencies"])
    mags = np.array(fft_result["magnitude"])
    
    # Step 2: Shaft features
    features = extract_shaft_features(freqs, mags, shaft_freq, time_signal=sig)
    
    # Step 3: Resolve bearing fault frequencies (3 methods, priority order)
    fault_freqs: dict[str, float] = {}
    bearing_info_source = None
    
    # Method A: Direct fault frequencies in Hz
    direct_hz = any(v is not None and v > 0 for v in [bpfo_hz, bpfi_hz, bsf_hz, ftf_hz])
    # Method A2: Fault frequency orders (multiples of shaft speed)
    direct_orders = any(v is not None and v > 0 for v in [bpfo_order, bpfi_order, bsf_order, ftf_order])

    if direct_hz or direct_orders:
        bearing_info_source = "user-provided frequencies" if direct_hz else "user-provided orders"
        for key, hz_val, order_val in [
            ("bpfo", bpfo_hz, bpfo_order),
            ("bpfi", bpfi_hz, bpfi_order),
            ("bsf", bsf_hz, bsf_order),
            ("ftf", ftf_hz, ftf_order),
        ]:
            if hz_val is not None and hz_val > 0:
                fault_freqs[key] = hz_val
            elif order_val is not None and order_val > 0:
                fault_freqs[key] = order_val * shaft_freq
    # Method B: Custom geometry
    elif bearing_n_balls and bearing_ball_dia_mm and bearing_pitch_dia_mm:
        bearing_info_source = "custom geometry"
        bf = compute_bearing_frequencies(
            rpm, bearing_n_balls, bearing_ball_dia_mm,
            bearing_pitch_dia_mm, bearing_contact_angle_deg, "custom",
        )
        fault_freqs = {"bpfo": bf.bpfo, "bpfi": bf.bpfi, "bsf": bf.bsf, "ftf": bf.ftf}
    # Method C: Database lookup
    elif bearing_designation:
        bearing = get_bearing(bearing_designation)
        if bearing:
            bearing_info_source = f"database ({bearing.name})"
            bf = compute_bearing_frequencies(
                rpm, bearing.n_balls, bearing.ball_dia, bearing.pitch_dia,
                bearing.contact_angle, bearing.name,
            )
            fault_freqs = {"bpfo": bf.bpfo, "bpfi": bf.bpfi, "bsf": bf.bsf, "ftf": bf.ftf}
    
    # Envelope analysis if any fault frequencies are available
    bearing_results = None
    if fault_freqs:
        env = envelope_spectrum(sig, sr)
        env_freqs = np.array(env["frequencies"])
        env_mags = np.array(env["envelope_spectrum"])
        bearing_results = {}
        for key, freq_val in fault_freqs.items():
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
        "bearing_info_source": bearing_info_source,
        "report_markdown": report,
    }


# ── Resource: analysis capabilities ──────────────────────────────────────

@mcp.resource("vibration-analysis://capabilities")
def analysis_capabilities() -> str:
    """List all analysis capabilities of this server."""
    return json.dumps({
        "signal_store": [
            "Server-side signal storage (load_signal → data_id)",
            "Compact summaries only — raw arrays never enter the conversation",
            "list_stored_signals to inspect what is loaded",
        ],
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
            "Custom geometry input (n_balls, ball_dia, pitch_dia, contact_angle)",
            "Direct fault-frequency input (BPFO/BPFI/BSF/FTF in Hz from manufacturer catalogs)",
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
