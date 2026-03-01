"""
Server-side data store for vibration signals.

Signals are stored in memory on the MCP server side, so they never need
to transit through the LLM conversation context. Claude only sees compact
summaries (statistics, peak lists, diagnosis reports).

Usage:
    store.put("my_signal", np.array([...]), sample_rate=26700.0, metadata={...})
    sig, sr, meta = store.get("my_signal")
    store.list_entries()
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from numpy.typing import NDArray


@dataclass
class DataEntry:
    """A stored signal with metadata."""
    signal: NDArray[np.floating]
    sample_rate: float
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    @property
    def n_samples(self) -> int:
        return self.signal.shape[0]

    @property
    def n_channels(self) -> int:
        return self.signal.shape[1] if self.signal.ndim > 1 else 1

    @property
    def duration_s(self) -> float:
        return self.n_samples / self.sample_rate if self.sample_rate > 0 else 0

    def summary(self) -> dict:
        """Return a compact summary (no raw data)."""
        sig = self.signal
        if sig.ndim == 1:
            sig = sig.reshape(-1, 1)

        channel_stats = {}
        labels = self.metadata.get(
            "axis_labels",
            ["X", "Y", "Z"][:sig.shape[1]] if sig.shape[1] <= 3
            else [f"CH{i}" for i in range(sig.shape[1])],
        )
        for i, label in enumerate(labels):
            col = sig[:, i]
            rms = float(np.sqrt(np.mean(col**2)))
            channel_stats[label] = {
                "mean": round(float(np.mean(col)), 6),
                "std": round(float(np.std(col)), 6),
                "rms": round(rms, 6),
                "peak": round(float(np.max(np.abs(col))), 6),
                "crest_factor": round(float(np.max(np.abs(col)) / rms), 2) if rms > 0 else 0,
                "kurtosis": round(float(_kurtosis(col)), 2),
            }

        return {
            "n_samples": self.n_samples,
            "n_channels": self.n_channels,
            "sample_rate_hz": self.sample_rate,
            "duration_s": round(self.duration_s, 4),
            "channel_stats": channel_stats,
            "metadata": {k: v for k, v in self.metadata.items() if k != "axis_labels"},
        }


def _kurtosis(x: NDArray) -> float:
    """Excess kurtosis (Fisher definition, normal = 0)."""
    n = len(x)
    if n < 4:
        return 0.0
    m = np.mean(x)
    s = np.std(x, ddof=1)
    if s < 1e-15:
        return 0.0
    return float(np.mean(((x - m) / s) ** 4) - 3.0)


class DataStore:
    """Simple in-memory store for vibration signals."""

    def __init__(self) -> None:
        self._entries: dict[str, DataEntry] = {}

    def put(
        self,
        data_id: str,
        signal: NDArray[np.floating],
        sample_rate: float,
        metadata: dict | None = None,
    ) -> str:
        """Store a signal. Returns the data_id."""
        self._entries[data_id] = DataEntry(
            signal=np.asarray(signal, dtype=np.float64),
            sample_rate=sample_rate,
            metadata=metadata or {},
        )
        return data_id

    def put_auto(
        self,
        signal: NDArray[np.floating],
        sample_rate: float,
        metadata: dict | None = None,
    ) -> str:
        """Store a signal with an auto-generated ID."""
        h = hashlib.md5(signal.tobytes()[:1024]).hexdigest()[:8]
        data_id = f"sig_{h}_{int(time.time()) % 100000}"
        return self.put(data_id, signal, sample_rate, metadata)

    def get(self, data_id: str) -> DataEntry | None:
        return self._entries.get(data_id)

    def remove(self, data_id: str) -> bool:
        return self._entries.pop(data_id, None) is not None

    def list_ids(self) -> list[str]:
        return list(self._entries.keys())

    def list_entries(self) -> list[dict]:
        """Return summaries of all stored entries."""
        return [
            {"data_id": k, **v.summary()}
            for k, v in self._entries.items()
        ]

    def load_from_file(
        self,
        file_path: str,
        sample_rate: float,
        sensor_name: str = "",
        axes: int = 3,
        data_id: str | None = None,
    ) -> tuple[str, dict]:
        """
        Load a .csv or .dat file directly into the store.
        Returns (data_id, summary_dict).

        For DATALOG2 .dat files: pass the **acquisition folder** (the
        directory containing device_config.json and the .dat files) to
        load_from_datalog2_folder() instead — it uses the SDK to decode
        the complex binary format correctly.
        """
        from pathlib import Path
        p = Path(file_path)

        if p.suffix == ".csv":
            data = np.loadtxt(str(p), delimiter=",", dtype=np.float64)
        elif p.suffix == ".dat":
            raw = np.fromfile(str(p), dtype=np.int16)
            data = raw.reshape(-1, axes).astype(np.float64)
            if "iis3dwb" in sensor_name.lower() or "ism330dhcx" in sensor_name.lower():
                sensitivity = 0.000122  # ±16g default
                data *= sensitivity
        else:
            raise ValueError(f"Unsupported file format: {p.suffix}")

        meta = {
            "source_file": p.name,
            "sensor": sensor_name,
        }
        if data_id is None:
            data_id = p.stem.replace(" ", "_")

        self.put(data_id, data, sample_rate, meta)
        entry = self._entries[data_id]
        return data_id, entry.summary()

    def load_from_datalog2_folder(
        self,
        acquisition_folder: str,
        sensor_name: str = "iis3dwb_acc",
        start_time: float = 0,
        end_time: float = -1,
        data_id: str | None = None,
    ) -> tuple[str, dict]:
        """
        Load data from a DATALOG2 acquisition folder using the STDATALOG SDK.

        The acquisition folder is the directory created by FP-SNS-DATALOG2
        (e.g., ``20260228_23_52_30/``) and must contain ``device_config.json``
        plus the ``.dat`` sensor files.

        This method properly decodes the interleaved binary format (with
        timestamps and protocol headers) — unlike the naive int16
        approach in ``load_from_file``.

        Args:
            acquisition_folder: Path to the DATALOG2 acquisition directory.
            sensor_name: Component name (e.g., 'iis3dwb_acc', 'ism330dhcx_acc').
            start_time: Start time in seconds (default: 0 = beginning).
            end_time: End time in seconds (default: -1 = entire file).
            data_id: Optional human-readable ID; auto-generated if omitted.

        Returns:
            (data_id, summary_dict)
        """
        from pathlib import Path
        acq_path = Path(acquisition_folder)

        # Verify the folder looks like a DATALOG2 acquisition
        config_file = acq_path / "device_config.json"
        if not config_file.exists():
            raise ValueError(
                f"Not a valid DATALOG2 acquisition folder: "
                f"'{acquisition_folder}' (missing device_config.json)."
            )

        try:
            from stdatalog_core.HSD.HSDatalog import HSDatalog
        except ImportError:
            raise ImportError(
                "STDATALOG-PYSDK is required to read DATALOG2 .dat files. "
                "Install it from https://github.com/STMicroelectronics/stdatalog-pysdk"
            )

        # Create HSD instance
        hsd_factory = HSDatalog()
        hsd = hsd_factory.create_hsd(str(acq_path))
        hsd.enable_timestamp_recovery(True)

        # Find the component
        component = HSDatalog.get_component(hsd, sensor_name)
        if component is None:
            # List available components to help the user
            all_comps = HSDatalog.get_all_components(hsd, only_active=True)
            available = [c.get("name", str(c)) if isinstance(c, dict) else str(c)
                         for c in (all_comps or [])]
            raise ValueError(
                f"Sensor '{sensor_name}' not found in acquisition. "
                f"Available components: {available}"
            )

        # Extract data as DataFrame(s)
        df_list = HSDatalog.get_dataframe(
            hsd, component,
            start_time=start_time, end_time=end_time,
        )
        if not df_list:
            raise ValueError(
                f"No data returned for sensor '{sensor_name}' in "
                f"'{acquisition_folder}'."
            )

        # Concatenate all chunks (for large files)
        import pandas as pd
        df = pd.concat(df_list, ignore_index=True)

        # Drop timestamp column if present (usually first column named 'Time')
        time_cols = [c for c in df.columns if "time" in c.lower() or "timestamp" in c.lower()]
        if time_cols:
            df = df.drop(columns=time_cols)

        data = df.to_numpy(dtype=np.float64)

        # Read ODR from device config for sample rate
        # The SDK provides two ODR values:
        #   - get_sensor_measodr(): the *measured* (actual) ODR from the hardware
        #     (e.g., 26584 Hz) — more accurate, accounts for crystal tolerance
        #   - get_sensor_odr(): the *nominal* (configured) ODR (e.g., 26667 Hz)
        # We prefer measodr because it gives correct frequency resolution in FFT.
        # The small difference (~0.3%) is normal hardware behavior.
        sample_rate = 0.0
        nominal_odr = 0.0
        try:
            odr = HSDatalog.get_sensor_measodr(hsd, component)
            if odr and float(odr) > 0:
                sample_rate = float(odr)
        except Exception:
            pass
        # Also grab nominal ODR for reference
        try:
            nom = HSDatalog.get_sensor_odr(hsd, component)
            if nom and float(nom) > 0:
                nominal_odr = float(nom)
        except Exception:
            pass
        if sample_rate <= 0:
            if nominal_odr > 0:
                sample_rate = nominal_odr
            else:
                sample_rate = 26667.0  # IIS3DWB default fallback

        meta = {
            "source_folder": acq_path.name,
            "sensor": sensor_name,
            "datalog2": True,
            "odr_hz": sample_rate,
            "nominal_odr_hz": nominal_odr if nominal_odr > 0 else sample_rate,
            "odr_note": (
                "odr_hz is the measured (actual) sample rate from the hardware. "
                "nominal_odr_hz is the configured value. Small differences (~0.3%) "
                "are normal due to crystal oscillator tolerance."
            ),
        }
        if data_id is None:
            data_id = f"{acq_path.name}_{sensor_name}".replace(" ", "_")

        self.put(data_id, data, sample_rate, meta)
        entry = self._entries[data_id]
        return data_id, entry.summary()


# Global singleton — shared across all tools in this server
store = DataStore()
