# Core types and interfaces
# Components
from .component import (Component, ComponentState, HealthCheckableComponent,
                        StartableComponent)
from .health import HealthMonitor
from .interfaces import HealthCheckable, Logger, Startable, Stoppable
from .orchestrator import LifecycleOrchestrator
# Provider integration
from .provider_adapter import ProviderComponent
# Services
from .registry import ComponentRegistry
from .types import ComponentNotFoundError, HealthStatus, LifecycleError

__all__ = [
    # Types
    "ComponentState",
    "HealthStatus",
    "LifecycleError",
    "ComponentNotFoundError",
    # Interfaces
    "Startable",
    "Stoppable",
    "HealthCheckable",
    "Logger",
    # Components
    "Component",
    "StartableComponent",
    "HealthCheckableComponent",
    "ProviderComponent",
    # Services
    "ComponentRegistry",
    "LifecycleOrchestrator",
    "HealthMonitor",
]


def create_lifecycle_system(logger=None):
    """Create a complete lifecycle management system.

    Returns:
        Tuple of (registry, orchestrator, health_monitor)
    """
    registry = ComponentRegistry(logger)
    orchestrator = LifecycleOrchestrator(registry, logger)
    health_monitor = HealthMonitor(registry, logger=logger)

    return registry, orchestrator, health_monitor
