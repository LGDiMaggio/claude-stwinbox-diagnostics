"""
Sensor configuration helpers for STEVAL-STWINBX1.

Provides recommended configurations for common use cases (vibration monitoring,
acoustic emission, environmental monitoring) based on FP-AI-MONITOR2 and
FP-SNS-DATALOG2 documentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SensorPreset:
    """Predefined sensor configuration for a specific use case."""
    name: str
    description: str
    sensor_id: int
    sensor_name: str
    odr: float
    full_scale: float
    use_case: str


# ---------------------------------------------------------------------------
# Recommended presets for vibration monitoring
# ---------------------------------------------------------------------------

VIBRATION_PRESETS = {
    "wideband_vibration": SensorPreset(
        name="wideband_vibration",
        description="IIS3DWB at maximum ODR for wideband vibration analysis (up to ~13 kHz bandwidth)",
        sensor_id=1,
        sensor_name="iis3dwb",
        odr=26667.0,
        full_scale=16.0,  # ±16g for industrial machinery
        use_case="bearing_fault_detection, high_frequency_analysis",
    ),
    "medium_vibration": SensorPreset(
        name="medium_vibration",
        description="ISM330DHCX accelerometer for medium-frequency vibration (up to ~3.3 kHz)",
        sensor_id=2,
        sensor_name="ism330dhcx_acc",
        odr=6667.0,
        full_scale=4.0,  # ±4g for general machinery
        use_case="unbalance_detection, misalignment, general_monitoring",
    ),
    "low_speed_vibration": SensorPreset(
        name="low_speed_vibration",
        description="ISM330DHCX at 1666 Hz for low-speed machinery monitoring",
        sensor_id=2,
        sensor_name="ism330dhcx_acc",
        odr=1666.0,
        full_scale=4.0,
        use_case="low_rpm_machines, fans, pumps",
    ),
    "ultrasound_acoustic": SensorPreset(
        name="ultrasound_acoustic",
        description="IMP23ABSU analog microphone for acoustic emission / ultrasound monitoring",
        sensor_id=5,
        sensor_name="imp23absu",
        odr=192000.0,
        full_scale=1.0,  # N/A for mic, placeholder
        use_case="acoustic_emission, ultrasound_classification, bearing_early_detection",
    ),
    "temperature_monitoring": SensorPreset(
        name="temperature_monitoring",
        description="STTS22H temperature sensor for thermal monitoring",
        sensor_id=7,
        sensor_name="stts22h",
        odr=1.0,
        full_scale=1.0,  # N/A
        use_case="overheating_detection, thermal_trending",
    ),
}


def get_preset(name: str) -> Optional[SensorPreset]:
    """Get a sensor preset by name."""
    return VIBRATION_PRESETS.get(name)


def list_presets() -> list[dict]:
    """List all available presets with their descriptions."""
    return [
        {
            "name": p.name,
            "description": p.description,
            "sensor": p.sensor_name,
            "sensor_id": p.sensor_id,
            "odr_hz": p.odr,
            "full_scale": p.full_scale,
            "use_case": p.use_case,
        }
        for p in VIBRATION_PRESETS.values()
    ]


def recommend_config(fault_type: str, rpm: Optional[float] = None) -> list[SensorPreset]:
    """
    Recommend sensor configurations based on the fault type to detect.
    
    Args:
        fault_type: Type of fault to detect (e.g., 'bearing', 'unbalance', 'acoustic')
        rpm: Machine RPM if known, helps select appropriate ODR
        
    Returns:
        List of recommended SensorPresets
    """
    recommendations = []
    fault_lower = fault_type.lower()

    if any(kw in fault_lower for kw in ["bearing", "bpfi", "bpfo", "bsf"]):
        # Bearing faults need high-frequency content for envelope analysis
        recommendations.append(VIBRATION_PRESETS["wideband_vibration"])
        recommendations.append(VIBRATION_PRESETS["temperature_monitoring"])

    elif any(kw in fault_lower for kw in ["unbalance", "imbalance", "misalignment", "looseness"]):
        # Mechanical faults are in lower frequency range (1x, 2x, 3x RPM)
        if rpm and rpm < 600:
            recommendations.append(VIBRATION_PRESETS["low_speed_vibration"])
        else:
            recommendations.append(VIBRATION_PRESETS["medium_vibration"])

    elif any(kw in fault_lower for kw in ["acoustic", "ultrasound", "cavitation"]):
        recommendations.append(VIBRATION_PRESETS["ultrasound_acoustic"])

    elif any(kw in fault_lower for kw in ["general", "baseline", "all"]):
        # General monitoring: use medium vibration + temperature
        recommendations.append(VIBRATION_PRESETS["medium_vibration"])
        recommendations.append(VIBRATION_PRESETS["temperature_monitoring"])

    else:
        # Default: wideband covers most cases
        recommendations.append(VIBRATION_PRESETS["wideband_vibration"])

    return recommendations
