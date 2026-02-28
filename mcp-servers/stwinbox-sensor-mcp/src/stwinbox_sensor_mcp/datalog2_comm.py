"""
FP-SNS-DATALOG2 integration via STDATALOG-PYSDK (HSDLink_v2).

Wraps HSDLink / HSDLink_v2 to provide programmatic control of data
acquisition on the STEVAL-STWINBX1.  When the SDK packages
(``stdatalog_core``, ``stdatalog_pnpl``) are not installed the module
degrades gracefully — all public helpers return an explanatory error
string instead of raising.

Installation
------------
The STDATALOG-PYSDK packages are **not** published on PyPI.  Install
from the cloned source or wheel files::

    git clone --recursive https://github.com/STMicroelectronics/stdatalog-pysdk.git
    cd stdatalog-pysdk
    pip install stdatalog_pnpl/      # dependency
    pip install stdatalog_core/      # main SDK

Alternatively install the bundled wheels from each sub-module's
``dist/`` directory.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from threading import Event
from typing import Any, Optional

log = logging.getLogger("stwinbox-sensor-mcp.datalog2")

# ---------------------------------------------------------------------------
# Conditional import — keep the module importable even without the SDK.
# ---------------------------------------------------------------------------
_SDK_AVAILABLE = False
_SDK_IMPORT_ERROR: Optional[str] = None

try:
    from stdatalog_core.HSD_link.HSDLink import HSDLink, SensorAcquisitionThread
    from stdatalog_pnpl.PnPLCmd import PnPLCMDManager
    _SDK_AVAILABLE = True
except ImportError as exc:
    _SDK_IMPORT_ERROR = (
        f"STDATALOG-PYSDK not installed ({exc}).  "
        "See https://github.com/STMicroelectronics/stdatalog-pysdk "
        "for installation instructions."
    )
    log.warning(_SDK_IMPORT_ERROR)


def sdk_available() -> bool:
    """Return *True* if the STDATALOG-PYSDK is importable."""
    return _SDK_AVAILABLE


def sdk_error_message() -> str:
    """Human-readable message explaining why the SDK is missing."""
    return _SDK_IMPORT_ERROR or ""


# ---------------------------------------------------------------------------
# DataLog2Manager — singleton-style manager for a single HSDLink session.
# ---------------------------------------------------------------------------

class DataLog2Manager:
    """Thin wrapper around HSDLink_v2.

    Only one instance should be alive at a time (mirrors the way the
    real hardware works — a single USB-HID session).
    """

    def __init__(self) -> None:
        self._hsd_link: Any = None          # HSDLink facade
        self._hsd_link_instance: Any = None  # HSDLink_v2 object
        self._connected: bool = False
        self._device_id: int = 0             # always device 0 (single board)
        self._acquisition_folder: Optional[str] = None
        self._logging_active: bool = False
        self._sensor_threads: list = []
        self._stop_flags: list[Event] = []
        self._sensor_files: list = []

    # -- connection ---------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self._connected and self._hsd_link_instance is not None

    def connect(
        self,
        acquisition_folder: Optional[str] = None,
        dev_com_type: str = "st_hsd",
    ) -> dict:
        """Connect to the STWIN.box via USB-HID (PnPL protocol).

        Parameters
        ----------
        acquisition_folder:
            Where to store acquisition data.  Defaults to
            ``~/STWIN_acquisitions``.
        dev_com_type:
            ``'st_hsd'`` for USB-HID (default) or ``'st_serial_datalog'``
            for serial/UART.

        Returns a JSON-serialisable dict with connection status.
        """
        if not _SDK_AVAILABLE:
            return {"error": sdk_error_message()}

        if self.is_connected:
            return {"status": "already_connected", "device_id": self._device_id}

        if acquisition_folder is None:
            acquisition_folder = str(
                Path.home() / "STWIN_acquisitions"
            )
        self._acquisition_folder = acquisition_folder
        os.makedirs(acquisition_folder, exist_ok=True)

        try:
            self._hsd_link = HSDLink()
            self._hsd_link_instance = self._hsd_link.create_hsd_link(
                dev_com_type=dev_com_type,
                acquisition_folder=acquisition_folder,
            )

            if self._hsd_link_instance is None:
                return {
                    "error": (
                        "No compatible device found.  Make sure the "
                        "STEVAL-STWINBX1 is connected via USB and "
                        "FP-SNS-DATALOG2 firmware is flashed."
                    )
                }

            self._connected = True
            self._device_id = 0

            # Gather basic info
            devices = self._hsd_link.get_devices(self._hsd_link_instance)
            fw_info = self._hsd_link.get_firmware_info(
                self._hsd_link_instance, self._device_id
            )

            return {
                "status": "connected",
                "device_id": self._device_id,
                "devices": devices if devices else [],
                "firmware_info": fw_info if fw_info else {},
                "acquisition_folder": self._acquisition_folder,
            }
        except Exception as exc:
            self._connected = False
            return {"error": f"Connection failed: {exc}"}

    def disconnect(self) -> dict:
        """Disconnect from the board and clean up resources."""
        if not self.is_connected:
            return {"status": "not_connected"}

        # Stop any running acquisition first
        if self._logging_active:
            self.stop_acquisition()

        try:
            # No explicit close on HSDLink facade — just discard references
            self._hsd_link_instance = None
            self._hsd_link = None
            self._connected = False
            return {"status": "disconnected"}
        except Exception as exc:
            return {"error": f"Disconnect failed: {exc}"}

    # -- device info --------------------------------------------------------

    def get_device_info(self) -> dict:
        """Return firmware info, device identity, and acquisition info."""
        if not self.is_connected:
            return {"error": "Not connected. Call connect() first."}

        d_id = self._device_id
        hl = self._hsd_link
        inst = self._hsd_link_instance

        try:
            result: dict[str, Any] = {
                "device_id": d_id,
                "firmware_info": hl.get_firmware_info(inst, d_id) or {},
            }

            # Try optional fields — some may not be available for all FW
            for key, fn in [
                ("device_info", lambda: hl.get_device_info(inst, d_id)),
                ("acquisition_info", lambda: hl.get_acquisition_info(inst, d_id)),
            ]:
                try:
                    result[key] = fn() or {}
                except Exception:
                    result[key] = {}

            result["acquisition_folder"] = self._acquisition_folder
            result["logging_active"] = self._logging_active
            return result
        except Exception as exc:
            return {"error": f"get_device_info failed: {exc}"}

    # -- sensor enumeration / configuration ---------------------------------

    def get_sensors(self, only_active: bool = False) -> dict:
        """List sensor components with their names and status."""
        if not self.is_connected:
            return {"error": "Not connected. Call connect() first."}

        d_id = self._device_id
        hl = self._hsd_link
        inst = self._hsd_link_instance

        try:
            names = hl.get_sensors_names(inst, d_id, only_active=only_active) or []
            sensors_out: list[dict] = []
            for name in names:
                info: dict[str, Any] = {"name": name}
                try:
                    info["enabled"] = hl.get_sensor_enabled(inst, d_id, sensor_name=name)
                except Exception:
                    info["enabled"] = None
                try:
                    info["odr"] = hl.get_sensor_odr(inst, d_id, sensor_name=name)
                except Exception:
                    info["odr"] = None
                try:
                    info["fs"] = hl.get_sensor_fs(inst, d_id, sensor_name=name)
                except Exception:
                    info["fs"] = None
                sensors_out.append(info)

            return {"device_id": d_id, "sensors": sensors_out}
        except Exception as exc:
            return {"error": f"get_sensors failed: {exc}"}

    def configure_sensor(
        self,
        sensor_name: str,
        enable: Optional[bool] = None,
        odr: Optional[int] = None,
        fs: Optional[int] = None,
    ) -> dict:
        """Configure a sensor component.

        Parameters
        ----------
        sensor_name:
            PnPL component name (e.g. ``'iis3dwb_acc'``, ``'ism330dhcx_acc'``).
        enable:
            ``True`` / ``False`` to enable / disable.
        odr:
            ODR enum index (see DTDL model for available values).
        fs:
            Full-scale enum index.
        """
        if not self.is_connected:
            return {"error": "Not connected. Call connect() first."}

        d_id = self._device_id
        hl = self._hsd_link
        inst = self._hsd_link_instance

        try:
            changes: list[str] = []

            if enable is not None:
                hl.set_sensor_enable(inst, d_id, enable, sensor_name=sensor_name)
                changes.append(f"enable={enable}")

            if odr is not None:
                hl.set_sensor_odr(inst, d_id, odr, sensor_name=sensor_name)
                changes.append(f"odr={odr}")

            if fs is not None:
                hl.set_sensor_fs(inst, d_id, fs, sensor_name=sensor_name)
                changes.append(f"fs={fs}")

            if not changes:
                return {"warning": "No parameters provided to change."}

            # Read back
            new_enabled = hl.get_sensor_enabled(inst, d_id, sensor_name=sensor_name)
            new_odr = hl.get_sensor_odr(inst, d_id, sensor_name=sensor_name)
            new_fs = hl.get_sensor_fs(inst, d_id, sensor_name=sensor_name)

            return {
                "sensor": sensor_name,
                "applied": changes,
                "current": {
                    "enabled": new_enabled,
                    "odr": new_odr,
                    "fs": new_fs,
                },
            }
        except Exception as exc:
            return {"error": f"configure_sensor failed: {exc}"}

    # -- acquisition control ------------------------------------------------

    def start_acquisition(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """Start data logging to the SD card.

        SD card must be inserted in the STWIN.box.

        Parameters
        ----------
        name:
            Human-readable acquisition name (stored in acquisition_info.json).
        description:
            Free-form description.
        """
        if not self.is_connected:
            return {"error": "Not connected. Call connect() first."}
        if self._logging_active:
            return {"error": "Acquisition already running. Stop it first."}

        d_id = self._device_id
        hl = self._hsd_link
        inst = self._hsd_link_instance

        try:
            # Set metadata if provided
            if name:
                hl.set_acquisition_name(inst, d_id, name)
            if description:
                hl.set_acquisition_description(inst, d_id, description)

            # Start — interface=1 means SD card logging
            res = hl.start_log(inst, d_id)
            self._logging_active = True

            # Optionally start sensor data threads for USB streaming + save
            sensor_names = hl.get_sensors_names(inst, d_id, only_active=True) or []

            # Create data files and streaming threads for each active sensor
            acq_folder = hl.get_acquisition_folder(inst)
            files_created: list[str] = []

            for sn in sensor_names:
                dat_path = os.path.join(acq_folder, f"{sn}.dat")
                try:
                    f = open(dat_path, "wb+")
                    self._sensor_files.append(f)
                    stop_flag = Event()
                    self._stop_flags.append(stop_flag)
                    thread = SensorAcquisitionThread(
                        stop_flag, inst, f, d_id, sn
                    )
                    thread.start()
                    self._sensor_threads.append(thread)
                    files_created.append(dat_path)
                except Exception as exc:
                    log.warning("Could not start thread for %s: %s", sn, exc)

            return {
                "status": "acquisition_started",
                "acquisition_folder": acq_folder,
                "active_sensors": sensor_names,
                "data_files": files_created,
                "tip": (
                    "Use datalog2_stop_acquisition when done.  "
                    "Data files (.dat) will be saved in the acquisition folder."
                ),
            }
        except Exception as exc:
            self._logging_active = False
            return {"error": f"start_acquisition failed: {exc}"}

    def stop_acquisition(self) -> dict:
        """Stop the running acquisition and save configuration files."""
        if not self.is_connected:
            return {"error": "Not connected. Call connect() first."}
        if not self._logging_active:
            return {"status": "no_acquisition_running"}

        d_id = self._device_id
        hl = self._hsd_link
        inst = self._hsd_link_instance

        try:
            # Stop streaming threads
            for sf in self._stop_flags:
                sf.set()
            # Brief pause for threads to finish
            time.sleep(0.5)
            # Close data files
            for f in self._sensor_files:
                try:
                    f.close()
                except Exception:
                    pass

            # Stop device logging
            hl.stop_log(inst, d_id)

            # Save config JSON files
            hl.save_json_device_file(inst, d_id)
            hl.save_json_acq_info_file(inst, d_id)

            acq_folder = hl.get_acquisition_folder(inst)

            # Clean up thread state
            self._stop_flags.clear()
            self._sensor_threads.clear()
            self._sensor_files.clear()
            self._logging_active = False

            # List files generated
            generated: list[str] = []
            if acq_folder and os.path.isdir(acq_folder):
                generated = os.listdir(acq_folder)

            return {
                "status": "acquisition_stopped",
                "acquisition_folder": acq_folder,
                "files": generated,
                "tip": (
                    "Use load_data_from_file with the .dat file path "
                    "to load the data, then pass result to the "
                    "vibration-analysis server's load_signal tool."
                ),
            }
        except Exception as exc:
            self._logging_active = False
            return {"error": f"stop_acquisition failed: {exc}"}

    def set_sw_tag(self, tag_id: int, on: bool) -> dict:
        """Set or unset a software tag during acquisition.

        Useful for labelling time segments (e.g. normal/abnormal).
        """
        if not self.is_connected:
            return {"error": "Not connected. Call connect() first."}
        if not self._logging_active:
            return {"error": "No acquisition running."}

        d_id = self._device_id
        hl = self._hsd_link
        inst = self._hsd_link_instance

        try:
            if on:
                hl.set_sw_tag_on_by_id(inst, d_id, tag_id)
            else:
                hl.set_sw_tag_off_by_id(inst, d_id, tag_id)
            return {"tag_id": tag_id, "state": "on" if on else "off"}
        except Exception as exc:
            return {"error": f"set_sw_tag failed: {exc}"}


# ---------------------------------------------------------------------------
# Module-level singleton — used by the MCP tool layer in server.py
# ---------------------------------------------------------------------------
datalog2 = DataLog2Manager()
