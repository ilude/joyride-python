"""Core types for lifecycle management."""

from enum import Enum


class HealthStatus(Enum):
    """Component health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class LifecycleError(Exception):
    """Base exception for lifecycle management errors."""

    pass


class ComponentNotFoundError(LifecycleError):
    """Exception raised when a component is not found."""

    pass
