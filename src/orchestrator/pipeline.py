import re
from .models import FirmwareArtifact, CalibrationResult, FirmwareValidationException

class HardwareCIValidator:
    """
    Validates firmware artifacts and evaluates pulse sequence calibration telemetry.
    """
    ALLOWED_FPGA_FAMILIES = {"Zynq-UltraScale+", "Kintex-7", "Artix-7", "PolarFire"}
    MAX_JITTER_PICOSECONDS = 50.0
    MAX_CLOCK_DRIFT_PPM = 2.0

    @classmethod
    def validate_firmware_artifact(cls, artifact: FirmwareArtifact) -> bool:
        if artifact.target_fpga_family not in cls.ALLOWED_FPGA_FAMILIES:
            raise FirmwareValidationException(f"Unsupported FPGA architecture: {artifact.target_fpga_family}")

        if artifact.size_bytes > artifact.max_allowed_bytes:
            raise FirmwareValidationException(
                f"Bitstream binary size ({artifact.size_bytes}B) exceeds max limit ({artifact.max_allowed_bytes}B)"
            )

        if not re.match(r"^[a-fA-F0-9]{64}$", artifact.sha256_hash):
            raise FirmwareValidationException("Invalid SHA256 checksum format")

        return True

    @classmethod
    def audit_pulse_calibration(cls, test_id: str, measured_jitter_ps: float, measured_drift_ppm: float) -> CalibrationResult:
        passed = (measured_jitter_ps <= cls.MAX_JITTER_PICOSECONDS) and (abs(measured_drift_ppm) <= cls.MAX_CLOCK_DRIFT_PPM)

        if passed:
            msg = f"Pulse alignment passed (jitter: {measured_jitter_ps:.1f}ps, drift: {measured_drift_ppm:.2f}ppm)"
        else:
            msg = f"Timing violation: jitter {measured_jitter_ps:.1f}ps (max {cls.MAX_JITTER_PICOSECONDS}ps) or drift {measured_drift_ppm:.2f}ppm (max {cls.MAX_CLOCK_DRIFT_PPM}ppm)"

        return CalibrationResult(
            test_id=test_id,
            passed=passed,
            jitter_picoseconds=measured_jitter_ps,
            clock_drift_ppm=measured_drift_ppm,
            status_message=msg
        )
