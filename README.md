# Quantum Hardware CI Orchestrator

Hardware-in-the-loop (HIL) test pipeline arbitrator and firmware deployment validator for quantum control stacks and embedded instruments.

## Features
- **Hardware Device Lease Arbitration**: Prevents concurrent test collision on physical AWG, qubit readout, and pulser testbenches.
- **Firmware Integrity & Constraint Verification**: Validates bitstream artifacts against target FPGA families and image size limits.
- **Pulse Sequence Calibration Auditing**: Simulates hardware loopback calibration and asserts timing jitter thresholds.

## Testing
```bash
pytest -v
```
