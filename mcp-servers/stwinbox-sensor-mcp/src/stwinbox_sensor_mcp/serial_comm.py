"""
Serial communication module for STEVAL-STWINBX1.

Handles USB/Serial connection to the STWIN.box board using the CLI interface
exposed by FP-AI-MONITOR2 / FP-SNS-DATALOG2 firmware.

The STWIN.box exposes a Virtual COM Port (VCP) over USB. Commands are sent
as text strings and responses are read line-by-line.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sensor definitions matching FP-AI-MONITOR2 sensor_info output
# ---------------------------------------------------------------------------

KNOWN_SENSORS = {
    0: {"name": "imp34dt05", "type": "MIC", "description": "Digital MEMS microphone"},
    1: {"name": "iis3dwb", "type": "ACC", "description": "Wideband 3-axis vibration sensor (up to 6 kHz)"},
    2: {"name": "ism330dhcx_acc", "type": "ACC", "description": "6-axis IMU - accelerometer"},
    3: {"name": "ism330dhcx_gyro", "type": "GYRO", "description": "6-axis IMU - gyroscope"},
    5: {"name": "imp23absu", "type": "MIC", "description": "Analog MEMS microphone (up to 80 kHz)"},
    6: {"name": "iis2iclx", "type": "ACC", "description": "2-axis digital inclinometer"},
    7: {"name": "stts22h", "type": "TEMP", "description": "Temperature sensor (±0.5°C)"},
    8: {"name": "ilps22qs", "type": "PRESS", "description": "Barometer (1.26 / 4 bar)"},
    9: {"name": "iis2dlpc", "type": "ACC", "description": "Low-power 3-axis accelerometer"},
    10: {"name": "iis2mdc", "type": "MAG", "description": "3-axis magnetometer"},
}


@dataclass
class SensorConfig:
    """Configuration state for a single sensor."""
    sensor_id: int
    name: str
    sensor_type: str
    enabled: bool = False
    odr: float = 0.0  # Output Data Rate in Hz
    full_scale: float = 0.0  # Full-scale range
    available_odrs: list[float] = field(default_factory=list)
    available_fs: list[float] = field(default_factory=list)


@dataclass
class BoardConnection:
    """Manages the serial connection to a STWIN.box board."""

    port: Optional[str] = None
    baudrate: int = 115200
    timeout: float = 2.0
    _serial: Optional[serial.Serial] = field(default=None, repr=False)
    _connected: bool = False
    firmware_info: str = ""
    uid: str = ""
    sensors: dict[int, SensorConfig] = field(default_factory=dict)

    @property
    def is_connected(self) -> bool:
        return self._connected and self._serial is not None and self._serial.is_open

    def connect(self, port: str, baudrate: int = 115200) -> str:
        """Open serial connection to the STWIN.box board."""
        if self.is_connected:
            self.disconnect()

        try:
            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
            self.port = port
            self.baudrate = baudrate
            self._connected = True
            time.sleep(1.0)  # Wait for board to stabilize after connection

            # Flush any pending data
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()

            # Try to get board info
            self._query_board_info()

            logger.info(f"Connected to STWIN.box on {port}")
            return f"Connected to STWIN.box on {port}. FW: {self.firmware_info}"

        except serial.SerialException as e:
            self._connected = False
            self._serial = None
            raise ConnectionError(f"Failed to connect to {port}: {e}")

    def disconnect(self) -> str:
        """Close the serial connection."""
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._connected = False
        self._serial = None
        self.port = None
        logger.info("Disconnected from STWIN.box")
        return "Disconnected from STWIN.box"

    def send_command(self, command: str, wait_lines: int = 10, timeout_s: float = 5.0) -> list[str]:
        """
        Send a CLI command to the board and collect response lines.
        
        Args:
            command: CLI command string (e.g. 'info', 'sensor_info')
            wait_lines: Maximum number of response lines to read
            timeout_s: Total timeout for reading response
            
        Returns:
            List of response lines (stripped)
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to STWIN.box. Call connect_board first.")

        # Send command
        cmd_bytes = (command.strip() + "\r\n").encode("utf-8")
        self._serial.write(cmd_bytes)
        self._serial.flush()

        # Collect response
        lines = []
        start = time.time()
        while len(lines) < wait_lines and (time.time() - start) < timeout_s:
            if self._serial.in_waiting > 0:
                raw = self._serial.readline()
                line = raw.decode("utf-8", errors="replace").strip()
                if line and not line.startswith("$"):  # Skip prompt chars
                    lines.append(line)
            else:
                time.sleep(0.05)

        return lines

    def _query_board_info(self) -> None:
        """Query firmware info and UID from the board."""
        try:
            info_lines = self.send_command("info", wait_lines=15)
            self.firmware_info = " | ".join(info_lines) if info_lines else "Unknown"

            uid_lines = self.send_command("uid", wait_lines=5)
            self.uid = uid_lines[0] if uid_lines else "Unknown"
        except Exception as e:
            logger.warning(f"Could not query board info: {e}")

    def query_sensors(self) -> dict[int, SensorConfig]:
        """Query available sensors from the board via sensor_info command."""
        try:
            lines = self.send_command("sensor_info", wait_lines=20)
            self.sensors = {}

            for line in lines:
                # Parse lines like: "iis3dwb    ID=1 , type=ACC"
                if "ID=" in line:
                    parts = line.split("ID=")
                    if len(parts) == 2:
                        name = parts[0].strip()
                        id_type = parts[1].split(",")
                        sensor_id = int(id_type[0].strip())
                        sensor_type = id_type[1].strip().replace("type=", "") if len(id_type) > 1 else "UNKNOWN"

                        self.sensors[sensor_id] = SensorConfig(
                            sensor_id=sensor_id,
                            name=name,
                            sensor_type=sensor_type,
                        )
        except Exception as e:
            logger.warning(f"Could not query sensors: {e}")
            # Fall back to known sensors
            for sid, info in KNOWN_SENSORS.items():
                self.sensors[sid] = SensorConfig(
                    sensor_id=sid,
                    name=info["name"],
                    sensor_type=info["type"],
                )

        return self.sensors

    def configure_sensor(self, sensor_id: int, enable: Optional[bool] = None,
                         odr: Optional[float] = None, full_scale: Optional[float] = None) -> str:
        """Configure a sensor's parameters."""
        results = []

        if enable is not None:
            val = 1 if enable else 0
            resp = self.send_command(f"sensor_set {sensor_id} enable {val}", wait_lines=3)
            results.extend(resp)

        if odr is not None:
            resp = self.send_command(f"sensor_set {sensor_id} ODR {odr}", wait_lines=3)
            results.extend(resp)

        if full_scale is not None:
            resp = self.send_command(f"sensor_set {sensor_id} FS {full_scale}", wait_lines=3)
            results.extend(resp)

        return "\n".join(results) if results else "No changes applied"

    def get_sensor_config(self, sensor_id: int) -> dict:
        """Get current configuration of a sensor."""
        lines = self.send_command(f"sensor_get {sensor_id} all", wait_lines=20, timeout_s=3.0)
        config = {"sensor_id": sensor_id, "raw_response": "\n".join(lines)}

        for line in lines:
            if "enable" in line.lower():
                config["enabled"] = "true" in line.lower()
            elif "nominal ODR" in line:
                try:
                    config["odr_hz"] = float(line.split("=")[1].split("Hz")[0].strip())
                except (ValueError, IndexError):
                    pass
            elif "fullScale" in line and "Available" not in line:
                try:
                    config["full_scale"] = float(line.split("=")[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass

        return config

    def acquire_data_samples(self, sensor_id: int, num_samples: int = 1024) -> list[list[float]]:
        """
        Acquire raw data samples from a sensor.
        
        This is a simplified acquisition that reads data via the CLI/serial interface.
        For high-speed acquisition (e.g. IIS3DWB @ 26.7 kHz), use the HSDatalog
        firmware with SD card logging and then read from the STDATALOG-PYSDK.
        
        For this MCP server, we support a "streaming" mode where samples are
        collected over serial. Each sample is expected as a comma-separated line
        of axis values (e.g., "0.0123, -0.5678, 9.8001" for 3-axis accelerometer).
        
        Args:
            sensor_id: ID of the sensor to read
            num_samples: Number of samples to acquire
            
        Returns:
            List of samples, each sample is a list of floats (one per axis)
        """
        # NOTE: Real implementation would depend on firmware protocol.
        # With FP-SNS-DATALOG2, data is typically logged to SD card.
        # This provides a serial-based fallback for lower-rate sensors.
        
        samples = []
        
        # Ensure sensor is enabled
        self.configure_sensor(sensor_id, enable=True)
        time.sleep(0.5)
        
        # For high-speed sensors, we would use a different protocol.
        # This is a placeholder for the CLI-based approach.
        logger.info(f"Acquiring {num_samples} samples from sensor {sensor_id}")
        
        # In a real implementation, this would read from the data stream.
        # For now, we return a message indicating the need for real firmware integration.
        raise NotImplementedError(
            "Direct serial streaming requires firmware-specific protocol implementation. "
            "For high-speed data, use FP-SNS-DATALOG2 with SD card logging, then read "
            "the .dat files using STDATALOG-PYSDK. See references/data-acquisition.md"
        )


def list_available_ports() -> list[dict[str, str]]:
    """List all available serial/COM ports on the system."""
    ports = serial.tools.list_ports.comports()
    return [
        {
            "port": p.device,
            "description": p.description,
            "manufacturer": p.manufacturer or "Unknown",
            "vid_pid": f"{p.vid:04X}:{p.pid:04X}" if p.vid and p.pid else "N/A",
        }
        for p in ports
    ]


# Global board connection instance
board = BoardConnection()
