"""Core types for lifecycle management."""

from enum import Enum


class LifecycleState(Enum):
    """Component lifecycle states."""
    STOPPED = "stopped"
    STARTING = "starting"
    STARTED = "started"
    STOPPING = "stopping"
    FAILED = "failed"


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


class InvalidStateTransitionError(LifecycleError):
    """Exception raised when an invalid state transition is attempted."""
    pass


# Valid state transitions - simple dictionary
VALID_TRANSITIONS = {
    LifecycleState.STOPPED: {LifecycleState.STARTING},
    LifecycleState.STARTING: {LifecycleState.STARTED, LifecycleState.FAILED},
    LifecycleState.STARTED: {LifecycleState.STOPPING, LifecycleState.FAILED},
    LifecycleState.STOPPING: {LifecycleState.STOPPED, LifecycleState.FAILED},
    LifecycleState.FAILED: {LifecycleState.STOPPED, LifecycleState.STARTING},
}


def validate_transition(from_state: LifecycleState, to_state: LifecycleState) -> None:
    """Validate state transition."""
    valid_targets = VALID_TRANSITIONS.get(from_state, set())
    if to_state not in valid_targets:
        raise InvalidStateTransitionError(
            f"Invalid transition: {from_state.value} -> {to_state.value}"
        )
