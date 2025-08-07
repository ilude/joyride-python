"""System event definitions for Joyride DNS Service."""

from enum import Enum
from typing import Any, Dict, List, Optional

from app.joyride.events import Event


class SystemEventType(str, Enum):
    """System event types."""

    # System lifecycle
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_RESTART = "system.restart"

    # Resource events
    MEMORY_PRESSURE = "system.memory.pressure"
    DISK_SPACE_LOW = "system.disk.space_low"
    CPU_HIGH_USAGE = "system.cpu.high_usage"
    NETWORK_INTERFACE_UP = "system.network.interface_up"
    NETWORK_INTERFACE_DOWN = "system.network.interface_down"

    # Service events
    SERVICE_STARTED = "system.service.started"
    SERVICE_STOPPED = "system.service.stopped"
    SERVICE_FAILED = "system.service.failed"
    SERVICE_RESTARTED = "system.service.restarted"

    # Health events
    HEALTH_CHECK_PASSED = "system.health.check_passed"
    HEALTH_CHECK_FAILED = "system.health.check_failed"
    HEALTH_STATUS_CHANGED = "system.health.status_changed"

    # Process events
    PROCESS_STARTED = "system.process.started"
    PROCESS_STOPPED = "system.process.stopped"
    PROCESS_CRASHED = "system.process.crashed"


class SystemEvent(Event):
    """Base system event."""

    def __init__(
        self,
        event_type: str,
        source: str,
        system_event_type: SystemEventType,
        hostname: str,
        **kwargs
    ):
        """Initialize system event."""
        self.system_event_type = system_event_type
        self.hostname = hostname
        self.system_info = kwargs.get("system_info", {})
        self.memory_usage = kwargs.get("memory_usage")
        self.cpu_usage = kwargs.get("cpu_usage")
        self.disk_usage = kwargs.get("disk_usage")
        self.load_average = kwargs.get("load_average")

        # Extract event-specific parameters and add to data
        event_data = kwargs.pop("data", {})
        
        # Move all extra kwargs into the data dict
        for key, value in list(kwargs.items()):
            if key not in ["event_id", "timestamp", "metadata"]:
                event_data[key] = kwargs.pop(key)

        # Add system data to event data
        event_data.update({
            "system_event_type": system_event_type.value,
            "hostname": hostname,
            "system_info": self.system_info,
        })
        if self.memory_usage is not None:
            event_data["memory_usage"] = self.memory_usage
        if self.cpu_usage is not None:
            event_data["cpu_usage"] = self.cpu_usage
        if self.disk_usage is not None:
            event_data["disk_usage"] = self.disk_usage
        if self.load_average is not None:
            event_data["load_average"] = self.load_average

        super().__init__(
            event_type=event_type or system_event_type.value,
            source=source,
            data=event_data,
            **kwargs
        )

    def _validate(self) -> None:
        """Validate system event data."""
        if not self._event_type:
            raise ValueError("event_type cannot be empty")
        if not self.hostname:
            raise ValueError("hostname cannot be empty")


class SystemResourceEvent(SystemEvent):
    """System resource monitoring event."""

    def __init__(
        self,
        system_event_type: SystemEventType,
        source: str,
        hostname: str,
        resource_type: str,
        current_value: float,
        unit: str,
        event_type: Optional[str] = None,
        **kwargs
    ):
        """Initialize system resource event."""
        self.resource_type = resource_type
        self.current_value = current_value
        self.threshold_value = kwargs.get("threshold_value")
        self.unit = unit
        self.trend_direction = kwargs.get("trend_direction")
        self.change_rate = kwargs.get("change_rate")
        self.duration_above_threshold = kwargs.get("duration_above_threshold")
        self.affected_services = kwargs.get("affected_services", [])
        self.recommended_action = kwargs.get("recommended_action")

        # Add resource data to event data
        event_data = kwargs.get("data", {})
        event_data.update({
            "resource_type": resource_type,
            "current_value": current_value,
            "unit": unit,
            "affected_services": self.affected_services,
        })
        if self.threshold_value is not None:
            event_data["threshold_value"] = self.threshold_value
        if self.trend_direction:
            event_data["trend_direction"] = self.trend_direction
        if self.change_rate is not None:
            event_data["change_rate"] = self.change_rate
        if self.duration_above_threshold is not None:
            event_data["duration_above_threshold"] = self.duration_above_threshold
        if self.recommended_action:
            event_data["recommended_action"] = self.recommended_action
        kwargs["data"] = event_data

        super().__init__(
            event_type=event_type or system_event_type.value,
            source=source,
            system_event_type=system_event_type,
            hostname=hostname,
            **kwargs
        )

    @property
    def is_critical(self) -> bool:
        """Check if resource usage is critical (>90%)."""
        return self.current_value > 90.0

    @property
    def is_warning(self) -> bool:
        """Check if resource usage is warning level (>80%)."""
        return self.current_value > 80.0


# Placeholder classes for other system events
class SystemServiceEvent(SystemEvent):
    pass


class SystemHealthEvent(SystemEvent):
    pass


class SystemProcessEvent(SystemEvent):
    pass


class SystemNetworkEvent(SystemEvent):
    pass
