# Core types
# Interfaces
from .interfaces import HealthCheckable, Logger, Startable, Stoppable
from .types import (
    ComponentNotFoundError,
    HealthStatus,
    InvalidStateTransitionError,
    LifecycleError,
    LifecycleState,
)

# Backward compatibility aliases (until migration is complete)
LifecycleComponent = None  # TODO: Implement in Step 2
LifecycleDependencyError = LifecycleError
LifecycleManager = None  # TODO: Implement in Step 4

__all__ = [
    # Types
    "LifecycleState",
    "HealthStatus",
    "LifecycleError",
    "ComponentNotFoundError",
    "InvalidStateTransitionError",
    
    # Interfaces
    "Startable",
    "Stoppable",
    "HealthCheckable",
    "Logger",
    
    # Backward compatibility
    "LifecycleComponent",
    "LifecycleDependencyError",
    "LifecycleManager",
]
