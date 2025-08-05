"""System lifecycle event definitions for the Joyride DNS Service."""

from datetime import datetime
from typing import Any, Dict, Optional

from ..core.event_base import JoyrideEvent


class JoyrideSystemEvent(JoyrideEvent):
    """Application lifecycle events."""

    def __init__(
        self,
        event_type: str,
        source: str,
        component: str,
        operation: str,
        status: str,
        error_message: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialize system event.

        Args:
            event_type: Type of system event
            source: Source component generating the event
            component: Component name
            operation: Operation performed (start, stop, reload, etc.)
            status: Operation status (success, failed, in_progress)
            error_message: Error message if operation failed
            configuration: Configuration changes
            data: Additional event data
            metadata: Additional event metadata
            timestamp: Event timestamp
        """
        event_data = data or {}
        event_data.update(
            {
                "component": component,
                "operation": operation,
                "status": status,
                "error_message": error_message,
                "configuration": configuration or {},
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
    def operation(self) -> str:
        """Get operation."""
        return self.data["operation"]

    @property
    def status(self) -> str:
        """Get status."""
        return self.data["status"]

    @property
    def error_message(self) -> Optional[str]:
        """Get error message."""
        return self.data["error_message"]

    @property
    def configuration(self) -> Dict[str, Any]:
        """Get configuration."""
        return self.data["configuration"]

    def _validate(self) -> None:
        """Validate system event data."""
        super()._validate()

        if not self.component:
            raise ValueError("Component name cannot be empty")

        if not self.operation:
            raise ValueError("Operation cannot be empty")

        if not self.status:
            raise ValueError("Status cannot be empty")
