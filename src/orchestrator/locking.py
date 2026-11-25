from typing import Dict, Optional
from .models import DeviceLease, DeviceType, DeviceBusyException

class HardwareLockManager:
    """
    Arbitrates exclusive hardware testbench leases across concurrent CI test runs.
    """
    def __init__(self):
        self._leases: Dict[str, DeviceLease] = {}

    def acquire_lease(self, device_id: str, device_type: DeviceType, pipeline_id: str, current_time_ts: float, ttl: float = 300.0) -> DeviceLease:
        # Check if existing lease is expired
        if device_id in self._leases:
            existing = self._leases[device_id]
            if current_time_ts - existing.acquired_at_ts > existing.ttl_seconds:
                # Expired lease reclaimed
                del self._leases[device_id]
            elif existing.pipeline_id != pipeline_id:
                raise DeviceBusyException(device_id=device_id, held_by=existing.pipeline_id)

        lease = DeviceLease(
            device_id=device_id,
            device_type=device_type,
            pipeline_id=pipeline_id,
            acquired_at_ts=current_time_ts,
            ttl_seconds=ttl
        )
        self._leases[device_id] = lease
        return lease

    def release_lease(self, device_id: str, pipeline_id: str) -> bool:
        if device_id in self._leases:
            if self._leases[device_id].pipeline_id == pipeline_id:
                del self._leases[device_id]
                return True
        return False

    def is_locked(self, device_id: str, current_time_ts: float) -> bool:
        if device_id not in self._leases:
            return False
        lease = self._leases[device_id]
        if current_time_ts - lease.acquired_at_ts > lease.ttl_seconds:
            del self._leases[device_id]
            return False
        return True
