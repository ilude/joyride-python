"""Test lifecycle types."""

import pytest

from app.joyride.injection.lifecycle.types import (
    HealthStatus,
    InvalidStateTransitionError,
    LifecycleState,
    validate_transition,
)


def test_lifecycle_states():
    """Test lifecycle state enum."""
    assert LifecycleState.STOPPED.value == "stopped"
    assert LifecycleState.STARTING.value == "starting"
    assert LifecycleState.STARTED.value == "started"
    assert LifecycleState.STOPPING.value == "stopping"
    assert LifecycleState.FAILED.value == "failed"


def test_health_status():
    """Test health status enum."""
    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.DEGRADED.value == "degraded"
    assert HealthStatus.UNHEALTHY.value == "unhealthy"
    assert HealthStatus.UNKNOWN.value == "unknown"


def test_valid_transitions():
    """Test valid state transitions."""
    # Valid transitions should not raise
    validate_transition(LifecycleState.STOPPED, LifecycleState.STARTING)
    validate_transition(LifecycleState.STARTING, LifecycleState.STARTED)
    validate_transition(LifecycleState.STARTED, LifecycleState.STOPPING)
    validate_transition(LifecycleState.STOPPING, LifecycleState.STOPPED)


def test_invalid_transitions():
    """Test invalid state transitions."""
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(LifecycleState.STOPPED, LifecycleState.STARTED)
    
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(LifecycleState.STARTED, LifecycleState.STARTING)
