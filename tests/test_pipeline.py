import pytest
from src.orchestrator.models import (
    DeviceType,
    FirmwareArtifact,
    DeviceBusyException,
    FirmwareValidationException
)
from src.orchestrator.locking import HardwareLockManager
from src.orchestrator.pipeline import HardwareCIValidator

def test_hardware_lease_acquisition_and_release():
    mgr = HardwareLockManager()
    time_now = 1000.0

    lease = mgr.acquire_lease("awg-slot-01", DeviceType.AWG, "pipeline-ci-101", time_now, ttl=60.0)
    assert lease.device_id == "awg-slot-01"
    assert mgr.is_locked("awg-slot-01", time_now + 10.0) is True

    # Same pipeline can refresh
    mgr.acquire_lease("awg-slot-01", DeviceType.AWG, "pipeline-ci-101", time_now + 20.0)

    # Different pipeline encounters busy error
    with pytest.raises(DeviceBusyException) as excinfo:
        mgr.acquire_lease("awg-slot-01", DeviceType.AWG, "pipeline-ci-102", time_now + 25.0)
    assert excinfo.value.held_by == "pipeline-ci-101"

    # Clean release
    assert mgr.release_lease("awg-slot-01", "pipeline-ci-101") is True
    assert mgr.is_locked("awg-slot-01", time_now + 30.0) is False

def test_hardware_lease_ttl_expiry():
    mgr = HardwareLockManager()
    time_now = 2000.0

    mgr.acquire_lease("readout-q0", DeviceType.READOUT_MODULE, "pipeline-ci-103", time_now, ttl=30.0)
    assert mgr.is_locked("readout-q0", time_now + 10.0) is True

    # After TTL, lock is automatically expired and reclaimable
    assert mgr.is_locked("readout-q0", time_now + 35.0) is False
    new_lease = mgr.acquire_lease("readout-q0", DeviceType.READOUT_MODULE, "pipeline-ci-104", time_now + 35.0)
    assert new_lease.pipeline_id == "pipeline-ci-104"

def test_firmware_validation_success():
    valid = FirmwareArtifact(
        artifact_id="fw-rev-42",
        target_fpga_family="Zynq-UltraScale+",
        size_bytes=4 * 1024 * 1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert HardwareCIValidator.validate_firmware_artifact(valid) is True

def test_firmware_validation_failures():
    # Unsupported architecture
    bad_arch = FirmwareArtifact(
        artifact_id="fw-rev-bad",
        target_fpga_family="Unsupported-Altera",
        size_bytes=1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    with pytest.raises(FirmwareValidationException) as e:
        HardwareCIValidator.validate_firmware_artifact(bad_arch)
    assert "Unsupported FPGA architecture" in str(e.value)

    # Oversized bitstream
    huge_fw = FirmwareArtifact(
        artifact_id="fw-rev-huge",
        target_fpga_family="Kintex-7",
        size_bytes=32 * 1024 * 1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    with pytest.raises(FirmwareValidationException) as e:
        HardwareCIValidator.validate_firmware_artifact(huge_fw)
    assert "Bitstream binary size" in str(e.value)

def test_pulse_calibration_audit():
    # Compliant pulse sequence
    res_pass = HardwareCIValidator.audit_pulse_calibration("cal-run-001", measured_jitter_ps=32.4, measured_drift_ppm=0.85)
    assert res_pass.passed is True
    assert "Pulse alignment passed" in res_pass.status_message

    # Timing jitter violation (>50ps)
    res_fail = HardwareCIValidator.audit_pulse_calibration("cal-run-002", measured_jitter_ps=68.2, measured_drift_ppm=0.50)
    assert res_fail.passed is False
    assert "Timing violation: jitter 68.2ps" in res_fail.status_message
