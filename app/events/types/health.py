"""Health status event definitions for the Joyride DNS Service."""

from datetime import datetime
from typing import Any, Dict, Optional, Union

from ..core.event_base import JoyrideEvent


class JoyrideHealthEvent(JoyrideEvent):
    """Health status events."""

    def __init__(
        self,
        event_type: str,
        source: str,
        component: str,
        health_status: str,
        check_name: str,
        check_result: bool,
        check_message: Optional[str] = None,
        check_duration: Optional[float] = None,
        metrics: Optional[Dict[str, Union[int, float, str]]] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialize health event.

        Args:
            event_type: Type of health event
            source: Source component generating the event
            component: Component being checked
            health_status: Overall health status (healthy, degraded, unhealthy)
            check_name: Name of the health check
            check_result: Health check result (True = healthy)
            check_message: Health check message
            check_duration: Health check duration in seconds
            metrics: Health metrics
            data: Additional event data
            metadata: Additional event metadata
            timestamp: Event timestamp
        """
        event_data = data or {}
        event_data.update(
            {
                "component": component,
                "health_status": health_status,
                "check_name": check_name,
                "check_result": check_result,
                "check_message": check_message,
                "check_duration": check_duration,
                "metrics": metrics or {},
            }
        )

        super().__init__(
            event_type=event_type,
            source=source,
            data=event_data,
            metadata=metadata,
            timestamp=timestamp,
        )

    @property
    def component(self) -> str:
        """Get component name."""
        return self.data["component"]

    @property
    def health_status(self) -> str:
        """Get health status."""
        return self.data["health_status"]

    @property
    def check_name(self) -> str:
        """Get check name."""
        return self.data["check_name"]

    @property
    def check_result(self) -> bool:
        """Get check result."""
        return self.data["check_result"]

    @property
    def check_message(self) -> Optional[str]:
        """Get check message."""
        return self.data["check_message"]

    @property
    def check_duration(self) -> Optional[float]:
        """Get check duration."""
        return self.data["check_duration"]

    @property
    def metrics(self) -> Dict[str, Union[int, float, str]]:
        """Get health metrics."""
        return self.data["metrics"]

    def _validate(self) -> None:
        """Validate health event data."""
        super()._validate()

        if not self.component:
            raise ValueError("Component name cannot be empty")

        if not self.health_status:
            raise ValueError("Health status cannot be empty")

        if not self.check_name:
            raise ValueError("Check name cannot be empty")

        valid_health_statuses = {"healthy", "degraded", "unhealthy"}
        if self.health_status not in valid_health_statuses:
            raise ValueError(f"Health status must be one of: {valid_health_statuses}")

        # Validate check duration if provided
        if self.check_duration is not None and self.check_duration < 0:
            raise ValueError("Check duration must be non-negative")
