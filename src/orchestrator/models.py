from dataclasses import dataclass
from enum import Enum
from typing import Optional

class DeviceType(str, Enum):
    AWG = "AWG"
    READOUT_MODULE = "READOUT_MODULE"
    PULSE_SEQUENCER = "PULSE_SEQUENCER"
    Q1ASM_CONTROLLER = "Q1ASM_CONTROLLER"

@dataclass
class DeviceLease:
    device_id: str
    device_type: DeviceType
    pipeline_id: str
    acquired_at_ts: float
    ttl_seconds: float = 300.0

@dataclass
class FirmwareArtifact:
    artifact_id: str
    target_fpga_family: str
    size_bytes: int
    sha256_hash: str
    max_allowed_bytes: int = 16 * 1024 * 1024  # 16 MB limit

@dataclass
class CalibrationResult:
    test_id: str
    passed: bool
    jitter_picoseconds: float
    clock_drift_ppm: float
    status_message: str

class DeviceBusyException(Exception):
    def __init__(self, device_id: str, held_by: str):
        super().__init__(f"Device {device_id} is currently locked by pipeline {held_by}")
        self.device_id = device_id
        self.held_by = held_by

class FirmwareValidationException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
