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


# Global singleton — shared across all tools in this server
store = DataStore()
