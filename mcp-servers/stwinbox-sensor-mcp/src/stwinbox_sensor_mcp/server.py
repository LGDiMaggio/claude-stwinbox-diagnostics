"""
STWIN.box Sensor MCP Server

FastMCP server exposing tools for communicating with the STEVAL-STWINBX1
SensorTile Wireless Industrial Node via USB/Serial.

Tools:
- list_serial_ports: List available COM ports
- connect_board: Connect to STWIN.box  
- disconnect_board: Disconnect from board
- get_board_info: Get firmware info and UID
- list_sensors: List all onboard sensors
- configure_sensor: Set ODR, FS, enable/disable
- get_sensor_config: Read current sensor settings
- apply_preset: Apply a predefined sensor configuration
- list_presets: Show available sensor presets
- recommend_sensor_config: Get config recommendations for a fault type
- acquire_data: Acquire samples (placeholder for real firmware integration)
- load_data_from_file: Load previously acquired data from .dat/.csv files
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from mcp.server.fastmcp import FastMCP

from .serial_comm import board, list_available_ports, KNOWN_SENSORS
from .sensor_config import get_preset, list_presets, recommend_config

# Configure logging to stderr (required for STDIO MCP servers)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("stwinbox-sensor-mcp")

# Initialize FastMCP server
mcp = FastMCP("stwinbox-sensor")


# ===========================================================================
# Connection Tools
# ===========================================================================

@mcp.tool()
def list_serial_ports() -> str:
    """List all available serial/COM ports on the system.
    
    Use this to find the COM port where the STEVAL-STWINBX1 is connected.
    Look for ports with 'STMicroelectronics' manufacturer or 'USB Serial Device'.
    """
    ports = list_available_ports()
    if not ports:
        return "No serial ports found. Ensure the STWIN.box is connected via USB-C."
    
    result = "Available serial ports:\n"
    for p in ports:
        result += f"  {p['port']}: {p['description']} (Manufacturer: {p['manufacturer']}, VID:PID={p['vid_pid']})\n"
    return result


@mcp.tool()
def connect_board(port: str, baudrate: int = 115200) -> str:
    """Connect to a STEVAL-STWINBX1 board via USB serial.
    
    Args:
        port: COM port (e.g., 'COM5' on Windows, '/dev/ttyACM0' on Linux)
        baudrate: Baud rate, default 115200
    """
    try:
        return board.connect(port, baudrate)
    except ConnectionError as e:
        return f"Error: {e}"


@mcp.tool()
def disconnect_board() -> str:
    """Disconnect from the currently connected STWIN.box board."""
    return board.disconnect()


@mcp.tool()
def get_board_info() -> str:
    """Get firmware version, UID, and connection status of the STWIN.box board."""
    if not board.is_connected:
        return "Not connected. Use connect_board first."
    
    return json.dumps({
        "connected": True,
        "port": board.port,
        "firmware_info": board.firmware_info,
        "uid": board.uid,
    }, indent=2)


# ===========================================================================
# Sensor Query Tools
# ===========================================================================

@mcp.tool()
def list_sensors() -> str:
    """List all onboard sensors of the STWIN.box with their IDs and types.
    
    Returns sensor name, ID, type (ACC, GYRO, MIC, TEMP, PRESS, MAG), 
    and description for each sensor. This information is needed to configure
    sensors and acquire data.
    """
    if board.is_connected:
        sensors = board.query_sensors()
    else:
        # Return known sensor map even without connection
        sensors = None

    result = "STEVAL-STWINBX1 Onboard Sensors:\n"
    result += "-" * 70 + "\n"
    result += f"{'ID':>3} | {'Name':<16} | {'Type':<6} | {'Description'}\n"
    result += "-" * 70 + "\n"

    sensor_data = sensors if sensors else {
        sid: type("", (), {"name": info["name"], "sensor_type": info["type"]})()
        for sid, info in KNOWN_SENSORS.items()
    }

    for sid in sorted(KNOWN_SENSORS.keys()):
        info = KNOWN_SENSORS[sid]
        result += f"{sid:>3} | {info['name']:<16} | {info['type']:<6} | {info['description']}\n"

    result += "-" * 70 + "\n"
    result += "\nKey sensors for vibration monitoring:\n"
    result += "  - IIS3DWB (ID=1): Best for wideband vibration, 26.7 kHz ODR\n"
    result += "  - ISM330DHCX (ID=2): Good for general vibration, up to 6.7 kHz\n"
    result += "  - IMP23ABSU (ID=5): Acoustic/ultrasound monitoring, up to 80 kHz\n"
    return result


@mcp.tool()
def get_sensor_config(sensor_id: int) -> str:
    """Get the current configuration of a sensor (ODR, full-scale, enabled state).
    
    Args:
        sensor_id: Sensor ID (use list_sensors to see available IDs)
    """
    if not board.is_connected:
        return "Not connected. Use connect_board first."
    
    config = board.get_sensor_config(sensor_id)
    return json.dumps(config, indent=2)


@mcp.tool()
def configure_sensor(
    sensor_id: int,
    enable: Optional[bool] = None,
    odr: Optional[float] = None,
    full_scale: Optional[float] = None,
) -> str:
    """Configure a sensor's parameters (enable/disable, ODR, full-scale).
    
    Args:
        sensor_id: Sensor ID (use list_sensors to see available IDs)
        enable: True to enable, False to disable
        odr: Output Data Rate in Hz (e.g., 26667 for IIS3DWB, 1666 for ISM330DHCX)
        full_scale: Full-scale range (e.g., 4.0 for ±4g, 16.0 for ±16g)
    """
    if not board.is_connected:
        return "Not connected. Use connect_board first."
    
    return board.configure_sensor(sensor_id, enable=enable, odr=odr, full_scale=full_scale)


# ===========================================================================
# Preset Tools
# ===========================================================================

@mcp.tool()
def list_sensor_presets() -> str:
    """List available sensor configuration presets for common monitoring scenarios.
    
    Presets include recommended ODR, full-scale, and sensor selection for:
    - Wideband vibration (bearing faults)
    - Medium vibration (unbalance, misalignment)
    - Low-speed vibration
    - Ultrasound/acoustic emission
    - Temperature monitoring
    """
    presets = list_presets()
    result = "Available Sensor Presets:\n\n"
    for p in presets:
        result += f"  [{p['name']}]\n"
        result += f"    {p['description']}\n"
        result += f"    Sensor: {p['sensor']} (ID={p['sensor_id']}), ODR={p['odr_hz']} Hz, FS={p['full_scale']}\n"
        result += f"    Use case: {p['use_case']}\n\n"
    return result


@mcp.tool()
def apply_preset(preset_name: str) -> str:
    """Apply a predefined sensor configuration preset to the board.
    
    Args:
        preset_name: Name of the preset (use list_sensor_presets to see options)
    """
    if not board.is_connected:
        return "Not connected. Use connect_board first."
    
    preset = get_preset(preset_name)
    if not preset:
        return f"Unknown preset '{preset_name}'. Use list_sensor_presets to see available presets."
    
    result = board.configure_sensor(
        preset.sensor_id,
        enable=True,
        odr=preset.odr,
        full_scale=preset.full_scale,
    )
    return f"Applied preset '{preset_name}' to {preset.sensor_name} (ID={preset.sensor_id}):\n{result}"


@mcp.tool()
def recommend_sensor_config(fault_type: str, rpm: Optional[float] = None) -> str:
    """Recommend sensor configurations for detecting a specific fault type.
    
    Args:
        fault_type: Type of fault to detect. Options: 'bearing', 'unbalance', 
                    'misalignment', 'looseness', 'acoustic', 'general'
        rpm: Machine RPM if known (helps optimize ODR selection)
    """
    recommendations = recommend_config(fault_type, rpm)
    if not recommendations:
        return f"No specific recommendation for fault type '{fault_type}'. Try 'general'."
    
    result = f"Recommended sensor configuration for '{fault_type}'"
    if rpm:
        result += f" at {rpm} RPM"
    result += ":\n\n"
    
    for r in recommendations:
        result += f"  Sensor: {r.sensor_name} (ID={r.sensor_id})\n"
        result += f"  ODR: {r.odr} Hz\n"
        result += f"  Full Scale: ±{r.full_scale}g\n"
        result += f"  Reason: {r.description}\n\n"
    
    return result


# ===========================================================================
# Data Acquisition Tools
# ===========================================================================

@mcp.tool()
def acquire_data(sensor_id: int, num_samples: int = 1024) -> str:
    """Acquire vibration/sensor data samples from a sensor.
    
    NOTE: For high-speed sensors (IIS3DWB @ 26.7 kHz), direct serial streaming
    is not reliable. Use FP-SNS-DATALOG2 firmware to log to SD card, then use
    load_data_from_file → load_signal (vibration-analysis server) to analyse.
    
    For lower-rate sensors (temperature, pressure), serial acquisition works
    and returns a compact summary (not raw samples).
    
    Args:
        sensor_id: Sensor ID to acquire from
        num_samples: Number of samples to acquire (default: 1024)
    """
    if not board.is_connected:
        return "Not connected. Use connect_board first."
    
    try:
        samples = board.acquire_data_samples(sensor_id, num_samples)
        # Return summary, not the full array
        arr = np.array(samples, dtype=np.float64)
        summary = {
            "sensor_id": sensor_id,
            "num_samples": len(samples),
            "mean": round(float(np.mean(arr)), 6),
            "std": round(float(np.std(arr)), 6),
            "min": round(float(np.min(arr)), 6),
            "max": round(float(np.max(arr)), 6),
            "preview": arr[:5].tolist(),
        }
        return json.dumps(summary)
    except NotImplementedError:
        return (
            "Direct serial acquisition not supported for this sensor.\n\n"
            "Recommended approach for high-speed data:\n"
            "1. Flash FP-SNS-DATALOG2 firmware to STWIN.box\n"
            "2. Configure sensors via device_config.json on SD card\n"
            "3. Press USR button to start/stop acquisition\n"
            "4. Read .dat files from SD card using load_data_from_file\n"
            "5. Then call load_signal on the vibration-analysis server\n\n"
            "See: https://github.com/STMicroelectronics/fp-sns-datalog2"
        )


@mcp.tool()
def load_data_from_file(
    file_path: str,
    sensor_name: str = "iis3dwb",
    axes: int = 3,
) -> str:
    """Load previously acquired sensor data from a .csv or .dat file.
    
    This reads data files produced by FP-SNS-DATALOG2 high-speed datalogger
    or exported via STDATALOG-PYSDK.
    
    Returns a compact summary (statistics, preview) and the absolute file path.
    **Do NOT paste the raw data into the conversation** — instead, pass the
    file_path to the vibration-analysis server's ``load_signal`` tool,
    which stores the signal server-side and returns a ``data_id`` for all
    subsequent analysis.
    
    Args:
        file_path: Path to the data file (.csv with columns per axis, or raw .dat)
        sensor_name: Name of the sensor that produced the data
        axes: Number of axes in the data (3 for accelerometer, 1 for microphone)
    """
    p = Path(file_path)
    if not p.exists():
        return f"File not found: {file_path}"
    
    try:
        if p.suffix == ".csv":
            data = np.loadtxt(str(p), delimiter=",", dtype=np.float64)
        elif p.suffix == ".dat":
            raw = np.fromfile(str(p), dtype=np.int16)
            data = raw.reshape(-1, axes).astype(np.float64)
            if "iis3dwb" in sensor_name.lower() or "ism330dhcx" in sensor_name.lower():
                sensitivity = 0.000122  # ±16g default
                data *= sensitivity
        else:
            return f"Unsupported file format: {p.suffix}. Use .csv or .dat"
        
        num_samples = data.shape[0]
        num_axes = data.shape[1] if data.ndim > 1 else 1
        
        summary = {
            "file": str(p.name),
            "file_path": str(p.absolute()),
            "sensor": sensor_name,
            "total_samples": num_samples,
            "axes": num_axes,
            "stats": {},
        }
        
        axis_labels = ["X", "Y", "Z"] if num_axes == 3 else [f"CH{i}" for i in range(num_axes)]
        for i in range(min(num_axes, 3)):
            col = data[:, i] if data.ndim > 1 else data
            rms = float(np.sqrt(np.mean(col**2)))
            summary["stats"][axis_labels[i]] = {
                "mean": round(float(np.mean(col)), 6),
                "std": round(float(np.std(col)), 6),
                "rms": round(rms, 6),
                "peak": round(float(np.max(np.abs(col))), 6),
                "crest_factor": round(float(np.max(np.abs(col)) / rms), 2) if rms > 0 else 0,
            }
        
        # Provide a 5-sample preview (tiny footprint)
        summary["preview_samples"] = (data[:5].tolist() if data.ndim > 1 else data[:5].tolist())
        
        summary["next_step"] = (
            "Pass file_path and the correct sample_rate to the "
            "vibration-analysis server's load_signal tool to store "
            "the signal server-side and get a data_id for analysis."
        )
        
        return json.dumps(summary, indent=2)
    
    except Exception as e:
        return f"Error loading data: {e}"


# ===========================================================================
# Resources (MCP Resources for context)
# ===========================================================================

@mcp.resource("stwinbox://sensors")
def sensor_catalog() -> str:
    """Complete catalog of STEVAL-STWINBX1 onboard sensors."""
    return json.dumps(KNOWN_SENSORS, indent=2)
