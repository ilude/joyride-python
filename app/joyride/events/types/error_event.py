"""Error condition event definitions for the Joyride DNS Service."""

from datetime import datetime
from typing import Any, Dict, Optional

from ..event import Event


class ErrorEvent(Event):
    """Error condition events."""

    def __init__(
        self,
        event_type: str,
        source: str,
        error_type: str,
        error_message: str,
        error_code: Optional[str] = None,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error",
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialize error event.

        Args:
            event_type: Type of error event
            source: Source component generating the event
            error_type: Error type/category
            error_message: Human-readable error message
            error_code: Error code identifier
            stack_trace: Error stack trace
            context: Error context information
            severity: Error severity (debug, info, warning, error, critical)
            data: Additional event data
            metadata: Additional event metadata
            timestamp: Event timestamp
        """
        event_data = data or {}
        event_data.update(
            {
                "error_type": error_type,
                "error_message": error_message,
                "error_code": error_code,
                "stack_trace": stack_trace,
                "context": context or {},
                "severity": severity,
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
    def error_type(self) -> str:
        """Get error type."""
        return self.data["error_type"]

    @property
    def error_message(self) -> str:
        """Get error message."""
        return self.data["error_message"]

    @property
    def error_code(self) -> Optional[str]:
        """Get error code."""
        return self.data["error_code"]

    @property
    def stack_trace(self) -> Optional[str]:
        """Get stack trace."""
        return self.data["stack_trace"]

    @property
    def context(self) -> Dict[str, Any]:
        """Get error context."""
        return self.data["context"]

    @property
    def severity(self) -> str:
        """Get error severity."""
        return self.data["severity"]

    def _validate(self) -> None:
        """Validate error event data."""
        super()._validate()

        if not self.error_type:
            raise ValueError("Error type cannot be empty")

        if not self.error_message:
            raise ValueError("Error message cannot be empty")

        valid_severities = {"debug", "info", "warning", "error", "critical"}
        if self.severity not in valid_severities:
            raise ValueError(f"Severity must be one of: {valid_severities}")
