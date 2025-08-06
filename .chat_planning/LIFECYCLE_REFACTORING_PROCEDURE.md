# Lifecycle Refactoring Procedure

## Overview

This document provides a detailed, step-by-step procedure for refactoring the `lifecycle.py` module according to SOLID principles and Python best practices. The refactoring will split the monolithic module into focused, single-responsibility classes organized in a proper directory structure.

## Target Directory Structure

```
app/joyride/injection/lifecycle/
├── __init__.py                     # Public API exports
├── enums.py                        # Lifecycle and health enums
├── exceptions.py                   # Lifecycle-specific exceptions
├── protocols.py                    # Interface definitions
├── component.py                    # Base component class
├── component_registry.py           # Component registration and lookup
├── dependency_graph.py             # Dependency management and ordering
├── state_machine.py                # State transition management
├── health_monitor.py               # Health checking and monitoring
├── lifecycle_orchestrator.py       # Startup/shutdown orchestration
├── provider_component.py           # Provider wrapper component
├── health_converters.py            # Health status conversion strategies
└── validators.py                   # Validation utilities
```

## Refactoring Steps

### Phase 1: Setup and Foundation (Critical Priority)

#### Step 1.1: Create Directory Structure

```bash
# Create the lifecycle subdirectory
mkdir -p app/joyride/injection/lifecycle

# Create empty files for each module
touch app/joyride/injection/lifecycle/__init__.py
touch app/joyride/injection/lifecycle/enums.py
touch app/joyride/injection/lifecycle/exceptions.py
touch app/joyride/injection/lifecycle/protocols.py
touch app/joyride/injection/lifecycle/component.py
touch app/joyride/injection/lifecycle/component_registry.py
touch app/joyride/injection/lifecycle/dependency_graph.py
touch app/joyride/injection/lifecycle/state_machine.py
touch app/joyride/injection/lifecycle/health_monitor.py
touch app/joyride/injection/lifecycle/lifecycle_orchestrator.py
touch app/joyride/injection/lifecycle/provider_component.py
touch app/joyride/injection/lifecycle/health_converters.py
touch app/joyride/injection/lifecycle/validators.py
```

#### Step 1.2: Extract Enums and Constants

**File: `app/joyride/injection/lifecycle/enums.py`**

```python
"""Lifecycle and health status enumerations."""

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


# Valid state transitions
VALID_STATE_TRANSITIONS = {
    LifecycleState.STOPPED: {LifecycleState.STARTING},
    LifecycleState.STARTING: {LifecycleState.STARTED, LifecycleState.FAILED},
    LifecycleState.STARTED: {LifecycleState.STOPPING, LifecycleState.FAILED},
    LifecycleState.STOPPING: {LifecycleState.STOPPED, LifecycleState.FAILED},
    LifecycleState.FAILED: {LifecycleState.STOPPED, LifecycleState.STARTING},
}
```

#### Step 1.3: Extract Exception Classes

**File: `app/joyride/injection/lifecycle/exceptions.py`**

```python
"""Lifecycle-specific exception classes."""


class LifecycleError(Exception):
    """Base exception for lifecycle management errors."""
    pass


class LifecycleDependencyError(LifecycleError):
    """Exception raised when there are dependency issues."""
    pass


class LifecycleTimeoutError(LifecycleError):
    """Exception raised when lifecycle operations timeout."""
    pass


class ComponentNotFoundError(LifecycleError):
    """Exception raised when a component is not found."""
    pass


class ComponentAlreadyRegisteredError(LifecycleError):
    """Exception raised when attempting to register a duplicate component."""
    pass


class InvalidStateTransitionError(LifecycleError):
    """Exception raised when an invalid state transition is attempted."""
    pass


class ComponentStartupFailedError(LifecycleError):
    """Exception raised when a component fails to start."""
    pass


class ComponentShutdownFailedError(LifecycleError):
    """Exception raised when a component fails to stop."""
    pass


class CircularDependencyError(LifecycleDependencyError):
    """Exception raised when a circular dependency is detected."""
    pass
```

#### Step 1.4: Define Protocol Interfaces

**File: `app/joyride/injection/lifecycle/protocols.py`**

```python
"""Protocol interfaces for lifecycle components."""

from typing import Protocol, Optional
from abc import abstractmethod

from .enums import HealthStatus


class Startable(Protocol):
    """Protocol for components that can be started."""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the component."""
        ...


class Stoppable(Protocol):
    """Protocol for components that can be stopped."""
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the component."""
        ...


class HealthCheckable(Protocol):
    """Protocol for components that support health checking."""
    
    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Perform health check on the component."""
        ...


class TimingTrackable(Protocol):
    """Protocol for components that track timing metrics."""
    
    def get_startup_time(self) -> Optional[float]:
        """Get component startup duration in seconds."""
        ...
    
    def get_shutdown_time(self) -> Optional[float]:
        """Get component shutdown duration in seconds."""
        ...


class DependencyAware(Protocol):
    """Protocol for components that have dependencies."""
    
    def add_dependency(self, component_name: str) -> None:
        """Add a dependency on another component."""
        ...
    
    def add_dependent(self, component_name: str) -> None:
        """Add a component that depends on this one."""
        ...


class LoggerProvider(Protocol):
    """Protocol for logger injection."""
    
    def info(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
    def debug(self, message: str) -> None: ...
```

### Phase 2: Core Component Extraction

#### Step 2.1: Create Validation Utilities

**File: `app/joyride/injection/lifecycle/validators.py`**

```python
"""Validation utilities for lifecycle components."""

from .enums import LifecycleState, VALID_STATE_TRANSITIONS
from .exceptions import InvalidStateTransitionError


class ComponentValidator:
    """Validates component names and operations."""
    
    @staticmethod
    def validate_name(name: str) -> None:
        """Validate component name.
        
        Args:
            name: Component name to validate
            
        Raises:
            ValueError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError("Component name must be a non-empty string")
        
        if not name.strip():
            raise ValueError("Component name cannot be empty or whitespace")
    
    @staticmethod
    def validate_dependency_name(dependency_name: str) -> None:
        """Validate dependency name.
        
        Args:
            dependency_name: Dependency name to validate
            
        Raises:
            ValueError: If dependency name is invalid
        """
        if not dependency_name or not isinstance(dependency_name, str):
            raise ValueError("Dependency name must be a non-empty string")


class StateTransitionValidator:
    """Validates state transitions."""
    
    @staticmethod
    def validate_transition(from_state: LifecycleState, to_state: LifecycleState) -> None:
        """Validate state transition.
        
        Args:
            from_state: Current state
            to_state: Target state
            
        Raises:
            InvalidStateTransitionError: If transition is invalid
        """
        valid_targets = VALID_STATE_TRANSITIONS.get(from_state, set())
        if to_state not in valid_targets:
            raise InvalidStateTransitionError(
                f"Invalid state transition: {from_state.value} -> {to_state.value}"
            )
```

#### Step 2.2: Create State Machine

**File: `app/joyride/injection/lifecycle/state_machine.py`**

```python
"""Component state management."""

import asyncio
import time
from typing import Optional

from .enums import LifecycleState
from .validators import StateTransitionValidator
from .protocols import LoggerProvider


class ComponentStateMachine:
    """Manages component state transitions in a thread-safe manner."""
    
    def __init__(self, name: str, logger: Optional[LoggerProvider] = None):
        """Initialize state machine.
        
        Args:
            name: Component name for logging
            logger: Optional logger for state changes
        """
        self.name = name
        self._state = LifecycleState.STOPPED
        self._state_lock = asyncio.Lock()
        self._startup_time: Optional[float] = None
        self._shutdown_time: Optional[float] = None
        self._logger = logger
    
    @property
    def state(self) -> LifecycleState:
        """Get current state."""
        return self._state
    
    async def transition_to(self, new_state: LifecycleState) -> None:
        """Transition to a new state.
        
        Args:
            new_state: Target state
            
        Raises:
            InvalidStateTransitionError: If transition is invalid
        """
        async with self._state_lock:
            StateTransitionValidator.validate_transition(self._state, new_state)
            
            old_state = self._state
            self._state = new_state
            
            if self._logger:
                self._logger.debug(
                    f"Component {self.name} transitioned: {old_state.value} -> {new_state.value}"
                )
    
    async def start_timing(self) -> None:
        """Begin timing startup operation."""
        self._startup_start = time.time()
    
    async def end_startup_timing(self) -> None:
        """End timing startup operation."""
        if hasattr(self, '_startup_start'):
            self._startup_time = time.time() - self._startup_start
            delattr(self, '_startup_start')
    
    async def start_shutdown_timing(self) -> None:
        """Begin timing shutdown operation."""
        self._shutdown_start = time.time()
    
    async def end_shutdown_timing(self) -> None:
        """End timing shutdown operation."""
        if hasattr(self, '_shutdown_start'):
            self._shutdown_time = time.time() - self._shutdown_start
            delattr(self, '_shutdown_start')
    
    def get_startup_time(self) -> Optional[float]:
        """Get startup duration in seconds."""
        return self._startup_time
    
    def get_shutdown_time(self) -> Optional[float]:
        """Get shutdown duration in seconds."""
        return self._shutdown_time
```

#### Step 2.3: Create Base Component Class

**File: `app/joyride/injection/lifecycle/component.py`**

```python
"""Base component implementation."""

import asyncio
from abc import ABC
from typing import Set, Optional

from .enums import LifecycleState, HealthStatus
from .state_machine import ComponentStateMachine
from .validators import ComponentValidator
from .protocols import (
    Startable,
    Stoppable, 
    HealthCheckable,
    TimingTrackable,
    DependencyAware,
    LoggerProvider
)


class BaseComponent(ABC, TimingTrackable, DependencyAware):
    """Base implementation for lifecycle components."""
    
    def __init__(self, name: str, logger: Optional[LoggerProvider] = None):
        """Initialize component.
        
        Args:
            name: Component name
            logger: Optional logger instance
        """
        ComponentValidator.validate_name(name)
        
        self.name = name
        self._state_machine = ComponentStateMachine(name, logger)
        self._dependencies: Set[str] = set()
        self._dependents: Set[str] = set()
        self._dependency_lock = asyncio.Lock()
        self._logger = logger
    
    @property
    def state(self) -> LifecycleState:
        """Get current lifecycle state."""
        return self._state_machine.state
    
    def add_dependency(self, component_name: str) -> None:
        """Add a dependency on another component.
        
        Args:
            component_name: Name of the component this depends on
        """
        ComponentValidator.validate_dependency_name(component_name)
        self._dependencies.add(component_name)
    
    def add_dependent(self, component_name: str) -> None:
        """Add a component that depends on this one.
        
        Args:
            component_name: Name of the component that depends on this
        """
        ComponentValidator.validate_dependency_name(component_name)
        self._dependents.add(component_name)
    
    @property
    def dependencies(self) -> Set[str]:
        """Get component dependencies."""
        return self._dependencies.copy()
    
    @property
    def dependents(self) -> Set[str]:
        """Get components that depend on this one."""
        return self._dependents.copy()
    
    def get_startup_time(self) -> Optional[float]:
        """Get component startup duration in seconds."""
        return self._state_machine.get_startup_time()
    
    def get_shutdown_time(self) -> Optional[float]:
        """Get component shutdown duration in seconds."""
        return self._state_machine.get_shutdown_time()
    
    def __str__(self) -> str:
        """String representation of component."""
        return f"{self.__class__.__name__}({self.name}, state={self.state.value})"
    
    def __repr__(self) -> str:
        """Developer representation of component."""
        return (
            f"{self.__class__.__name__}(name={self.name!r}, "
            f"state={self.state.value})"
        )


class LifecycleComponent(BaseComponent, Startable, Stoppable, HealthCheckable):
    """Full-featured lifecycle component with all capabilities."""
    
    async def start(self) -> None:
        """Start the component. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement start()")
    
    async def stop(self) -> None:
        """Stop the component. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement stop()")
    
    async def health_check(self) -> HealthStatus:
        """Perform health check. Default implementation based on state."""
        if self.state == LifecycleState.STARTED:
            return HealthStatus.HEALTHY
        elif self.state == LifecycleState.FAILED:
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.UNKNOWN
```

### Phase 3: Service Layer Extraction

#### Step 3.1: Create Component Registry

**File: `app/joyride/injection/lifecycle/component_registry.py`**

```python
"""Component registration and lookup service."""

import asyncio
from typing import Dict, List, Optional

from .component import BaseComponent
from .exceptions import ComponentNotFoundError, ComponentAlreadyRegisteredError
from .protocols import LoggerProvider


class ComponentRegistry:
    """Manages component registration and lookup."""
    
    def __init__(self, logger: Optional[LoggerProvider] = None):
        """Initialize component registry.
        
        Args:
            logger: Optional logger instance
        """
        self._components: Dict[str, BaseComponent] = {}
        self._registry_lock = asyncio.Lock()
        self._logger = logger
    
    async def register(self, component: BaseComponent) -> None:
        """Register a component.
        
        Args:
            component: Component to register
            
        Raises:
            ComponentAlreadyRegisteredError: If component name already exists
        """
        async with self._registry_lock:
            if component.name in self._components:
                raise ComponentAlreadyRegisteredError(
                    f"Component '{component.name}' is already registered"
                )
            
            self._components[component.name] = component
            
            if self._logger:
                self._logger.info(f"Registered component: {component.name}")
    
    async def unregister(self, name: str) -> None:
        """Unregister a component.
        
        Args:
            name: Component name to unregister
            
        Raises:
            ComponentNotFoundError: If component not found
        """
        async with self._registry_lock:
            if name not in self._components:
                raise ComponentNotFoundError(f"Component '{name}' is not registered")
            
            component = self._components[name]
            
            # Validate component can be unregistered
            if component.state not in (LifecycleState.STOPPED, LifecycleState.FAILED):
                raise ValueError(
                    f"Component '{name}' must be stopped before unregistering"
                )
            
            del self._components[name]
            
            if self._logger:
                self._logger.info(f"Unregistered component: {name}")
    
    async def get(self, name: str) -> BaseComponent:
        """Get a component by name.
        
        Args:
            name: Component name
            
        Returns:
            The component instance
            
        Raises:
            ComponentNotFoundError: If component not found
        """
        async with self._registry_lock:
            if name not in self._components:
                raise ComponentNotFoundError(f"Component '{name}' not found")
            
            return self._components[name]
    
    async def get_optional(self, name: str) -> Optional[BaseComponent]:
        """Get a component by name, returning None if not found.
        
        Args:
            name: Component name
            
        Returns:
            The component instance or None
        """
        async with self._registry_lock:
            return self._components.get(name)
    
    async def list_names(self) -> List[str]:
        """Get list of all registered component names.
        
        Returns:
            List of component names
        """
        async with self._registry_lock:
            return list(self._components.keys())
    
    async def list_components(self) -> List[BaseComponent]:
        """Get list of all registered components.
        
        Returns:
            List of components
        """
        async with self._registry_lock:
            return list(self._components.values())
    
    async def count(self) -> int:
        """Get count of registered components.
        
        Returns:
            Number of registered components
        """
        async with self._registry_lock:
            return len(self._components)
    
    async def clear(self) -> None:
        """Clear all registered components."""
        async with self._registry_lock:
            self._components.clear()
            
            if self._logger:
                self._logger.info("Cleared all components from registry")
```

#### Step 3.2: Create Dependency Graph Manager

**File: `app/joyride/injection/lifecycle/dependency_graph.py`**

```python
"""Dependency graph management and resolution."""

import asyncio
from typing import Dict, List, Set

from .component_registry import ComponentRegistry
from .exceptions import CircularDependencyError, ComponentNotFoundError
from .protocols import LoggerProvider


class DependencyGraph:
    """Manages component dependencies and resolution order."""
    
    def __init__(self, registry: ComponentRegistry, logger: Optional[LoggerProvider] = None):
        """Initialize dependency graph.
        
        Args:
            registry: Component registry
            logger: Optional logger instance
        """
        self._registry = registry
        self._graph_lock = asyncio.Lock()
        self._logger = logger
    
    async def add_dependency(self, component_name: str, dependency_name: str) -> None:
        """Add a dependency between components.
        
        Args:
            component_name: Name of component that depends on dependency
            dependency_name: Name of dependency component
            
        Raises:
            ComponentNotFoundError: If components not found
            CircularDependencyError: If circular dependency detected
        """
        async with self._graph_lock:
            # Validate components exist
            component = await self._registry.get(component_name)
            await self._registry.get(dependency_name)  # Validate exists
            
            # Check for circular dependencies
            if await self._has_circular_dependency(component_name, dependency_name):
                raise CircularDependencyError(
                    f"Adding dependency would create circular dependency: "
                    f"{component_name} -> {dependency_name}"
                )
            
            # Add dependency relationships
            component.add_dependency(dependency_name)
            dependency_component = await self._registry.get(dependency_name)
            dependency_component.add_dependent(component_name)
            
            if self._logger:
                self._logger.info(
                    f"Added dependency: {component_name} depends on {dependency_name}"
                )
    
    async def _has_circular_dependency(self, component_name: str, new_dependency: str) -> bool:
        """Check if adding a dependency would create a circular dependency.
        
        Args:
            component_name: Component that would depend on new_dependency
            new_dependency: New dependency to check
            
        Returns:
            True if circular dependency would be created
        """
        # Check if new_dependency already depends on component_name
        visited = set()
        
        async def check_path(current: str, target: str) -> bool:
            if current == target:
                return True
            if current in visited:
                return False
            
            visited.add(current)
            
            current_component = await self._registry.get_optional(current)
            if current_component:
                for dep in current_component.dependencies:
                    if await check_path(dep, target):
                        return True
            
            return False
        
        return await check_path(new_dependency, component_name)
    
    async def get_startup_order(self) -> List[str]:
        """Get component startup order based on dependencies.
        
        Returns:
            List of component names in startup order
            
        Raises:
            CircularDependencyError: If circular dependencies exist
        """
        async with self._graph_lock:
            components = await self._registry.list_components()
            
            # Topological sort for startup order
            visited = set()
            temp_visited = set()
            order = []
            
            async def visit(name: str):
                if name in temp_visited:
                    raise CircularDependencyError(
                        f"Circular dependency detected involving {name}"
                    )
                if name in visited:
                    return
                
                temp_visited.add(name)
                component = await self._registry.get(name)
                
                # Visit dependencies first
                for dep_name in component.dependencies:
                    await visit(dep_name)
                
                temp_visited.remove(name)
                visited.add(name)
                order.append(name)
            
            # Visit all components
            for component in components:
                if component.name not in visited:
                    await visit(component.name)
            
            return order
    
    async def get_shutdown_order(self) -> List[str]:
        """Get component shutdown order (reverse of startup order).
        
        Returns:
            List of component names in shutdown order
        """
        startup_order = await self.get_startup_order()
        return list(reversed(startup_order))
    
    async def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get the complete dependency graph.
        
        Returns:
            Dictionary mapping component names to their dependencies
        """
        async with self._graph_lock:
            components = await self._registry.list_components()
            graph = {}
            
            for component in components:
                graph[component.name] = list(component.dependencies)
            
            return graph
```

### Phase 4: Specialized Components

#### Step 4.1: Create Health Status Converters

**File: `app/joyride/injection/lifecycle/health_converters.py`**

```python
"""Health status conversion strategies."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from .enums import HealthStatus


class HealthStatusConverter(ABC):
    """Abstract base class for health status converters."""
    
    @abstractmethod
    def can_convert(self, raw_status: Any) -> bool:
        """Check if this converter can handle the given status type.
        
        Args:
            raw_status: Raw status value to check
            
        Returns:
            True if this converter can handle the status
        """
        pass
    
    @abstractmethod
    def convert(self, raw_status: Any) -> HealthStatus:
        """Convert raw status to HealthStatus enum.
        
        Args:
            raw_status: Raw status value
            
        Returns:
            Converted HealthStatus
        """
        pass


class BooleanHealthConverter(HealthStatusConverter):
    """Converts boolean values to health status."""
    
    def can_convert(self, raw_status: Any) -> bool:
        """Check if status is a boolean."""
        return isinstance(raw_status, bool)
    
    def convert(self, raw_status: bool) -> HealthStatus:
        """Convert boolean to health status."""
        return HealthStatus.HEALTHY if raw_status else HealthStatus.UNHEALTHY


class StringHealthConverter(HealthStatusConverter):
    """Converts string values to health status."""
    
    def __init__(self):
        self._mapping = {
            "healthy": HealthStatus.HEALTHY,
            "degraded": HealthStatus.DEGRADED,
            "unhealthy": HealthStatus.UNHEALTHY,
            "unknown": HealthStatus.UNKNOWN,
            "ok": HealthStatus.HEALTHY,
            "good": HealthStatus.HEALTHY,
            "bad": HealthStatus.UNHEALTHY,
            "error": HealthStatus.UNHEALTHY,
        }
    
    def can_convert(self, raw_status: Any) -> bool:
        """Check if status is a string."""
        return isinstance(raw_status, str)
    
    def convert(self, raw_status: str) -> HealthStatus:
        """Convert string to health status."""
        return self._mapping.get(raw_status.lower(), HealthStatus.UNKNOWN)


class HealthStatusEnumConverter(HealthStatusConverter):
    """Passes through HealthStatus enum values."""
    
    def can_convert(self, raw_status: Any) -> bool:
        """Check if status is already a HealthStatus."""
        return isinstance(raw_status, HealthStatus)
    
    def convert(self, raw_status: HealthStatus) -> HealthStatus:
        """Return the HealthStatus as-is."""
        return raw_status


class HealthConverterRegistry:
    """Registry for health status converters."""
    
    def __init__(self):
        self._converters = [
            HealthStatusEnumConverter(),
            BooleanHealthConverter(),
            StringHealthConverter(),
        ]
    
    def convert(self, raw_status: Any) -> HealthStatus:
        """Convert raw status using appropriate converter.
        
        Args:
            raw_status: Raw status value
            
        Returns:
            Converted HealthStatus
        """
        for converter in self._converters:
            if converter.can_convert(raw_status):
                return converter.convert(raw_status)
        
        # Default to UNKNOWN for unsupported types
        return HealthStatus.UNKNOWN
    
    def register_converter(self, converter: HealthStatusConverter) -> None:
        """Register a new converter.
        
        Args:
            converter: Converter to register
        """
        # Insert at beginning to allow overriding defaults
        self._converters.insert(0, converter)
```

#### Step 4.2: Create Health Monitor

**File: `app/joyride/injection/lifecycle/health_monitor.py`**

```python
"""Health monitoring service."""

import asyncio
from typing import Dict, Optional

from .component_registry import ComponentRegistry
from .enums import HealthStatus
from .health_converters import HealthConverterRegistry
from .protocols import LoggerProvider, HealthCheckable


class HealthMonitor:
    """Monitors component health independently."""
    
    def __init__(
        self,
        registry: ComponentRegistry,
        check_interval: float = 30.0,
        logger: Optional[LoggerProvider] = None
    ):
        """Initialize health monitor.
        
        Args:
            registry: Component registry
            check_interval: Health check interval in seconds
            logger: Optional logger instance
        """
        self._registry = registry
        self._check_interval = check_interval
        self._logger = logger
        self._converter_registry = HealthConverterRegistry()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    async def start_monitoring(self) -> None:
        """Start periodic health check monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            return  # Already running
        
        self._shutdown_event.clear()
        self._monitoring_task = asyncio.create_task(self._health_check_loop())
        
        if self._logger:
            self._logger.info("Started health check monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop periodic health check monitoring."""
        self._shutdown_event.set()
        
        if self._monitoring_task and not self._monitoring_task.done():
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
        
        if self._logger:
            self._logger.info("Stopped health check monitoring")
    
    async def check_all(self) -> Dict[str, HealthStatus]:
        """Perform health check on all components.
        
        Returns:
            Dictionary mapping component names to their health status
        """
        results = {}
        components = await self._registry.list_components()
        
        for component in components:
            try:
                if isinstance(component, HealthCheckable):
                    raw_status = await component.health_check()
                    results[component.name] = self._converter_registry.convert(raw_status)
                else:
                    # Default health based on state for non-health-checkable components
                    results[component.name] = await component.health_check()
            except Exception as e:
                if self._logger:
                    self._logger.warning(
                        f"Health check failed for component {component.name}: {e}"
                    )
                results[component.name] = HealthStatus.UNHEALTHY
        
        return results
    
    async def check_component(self, name: str) -> HealthStatus:
        """Perform health check on a specific component.
        
        Args:
            name: Component name
            
        Returns:
            Component health status
        """
        component = await self._registry.get(name)
        
        try:
            if isinstance(component, HealthCheckable):
                raw_status = await component.health_check()
                return self._converter_registry.convert(raw_status)
            else:
                return await component.health_check()
        except Exception as e:
            if self._logger:
                self._logger.warning(
                    f"Health check failed for component {name}: {e}"
                )
            return HealthStatus.UNHEALTHY
    
    def set_check_interval(self, interval: float) -> None:
        """Set health check interval.
        
        Args:
            interval: Health check interval in seconds
        """
        if interval <= 0:
            raise ValueError("Health check interval must be positive")
        
        self._check_interval = interval
        
        if self._logger:
            self._logger.info(f"Health check interval set to {interval}s")
    
    def get_check_interval(self) -> float:
        """Get current health check interval."""
        return self._check_interval
    
    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        while not self._shutdown_event.is_set():
            try:
                # Wait for either shutdown event or interval timeout
                await asyncio.wait_for(
                    self._shutdown_event.wait(), timeout=self._check_interval
                )
                break  # Shutdown event was set
            except asyncio.TimeoutError:
                pass  # Timeout reached, perform health checks
            
            try:
                health_results = await self.check_all()
                
                # Log unhealthy components
                unhealthy = [
                    name for name, status in health_results.items()
                    if status == HealthStatus.UNHEALTHY
                ]
                
                if unhealthy and self._logger:
                    self._logger.warning(f"Unhealthy components detected: {unhealthy}")
            
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error during health check monitoring: {e}")
```

### Phase 5: Final Integration

#### Step 5.1: Create Lifecycle Orchestrator

**File: `app/joyride/injection/lifecycle/lifecycle_orchestrator.py`**

```python
"""Lifecycle orchestration service."""

import asyncio
from typing import List, Optional

from .component_registry import ComponentRegistry
from .dependency_graph import DependencyGraph
from .health_monitor import HealthMonitor
from .enums import LifecycleState
from .exceptions import (
    LifecycleError,
    LifecycleTimeoutError,
    ComponentStartupFailedError,
    ComponentShutdownFailedError
)
from .protocols import LoggerProvider, Startable, Stoppable


class LifecycleOrchestrator:
    """Orchestrates component startup and shutdown."""
    
    def __init__(
        self,
        registry: ComponentRegistry,
        dependency_graph: DependencyGraph,
        health_monitor: Optional[HealthMonitor] = None,
        startup_timeout: float = 30.0,
        shutdown_timeout: float = 30.0,
        logger: Optional[LoggerProvider] = None
    ):
        """Initialize lifecycle orchestrator.
        
        Args:
            registry: Component registry
            dependency_graph: Dependency graph manager
            health_monitor: Optional health monitor
            startup_timeout: Maximum time to wait for component startup
            shutdown_timeout: Maximum time to wait for component shutdown
            logger: Optional logger instance
        """
        self._registry = registry
        self._dependency_graph = dependency_graph
        self._health_monitor = health_monitor
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        self._logger = logger
    
    async def start_all(self) -> None:
        """Start all components in dependency order.
        
        Raises:
            LifecycleError: If any component fails to start
        """
        startup_order = await self._dependency_graph.get_startup_order()
        
        if self._logger:
            self._logger.info(f"Starting components in order: {startup_order}")
        
        for name in startup_order:
            component = await self._registry.get(name)
            
            if component.state != LifecycleState.STOPPED:
                if self._logger:
                    self._logger.warning(
                        f"Component {name} is not in stopped state, skipping"
                    )
                continue
            
            await self._start_component_internal(component)
        
        # Start health monitoring if available
        if self._health_monitor:
            await self._health_monitor.start_monitoring()
        
        if self._logger:
            self._logger.info("All components started successfully")
    
    async def stop_all(self) -> None:
        """Stop all components in reverse dependency order.
        
        Raises:
            LifecycleError: If any component fails to stop
        """
        # Stop health monitoring first
        if self._health_monitor:
            await self._health_monitor.stop_monitoring()
        
        shutdown_order = await self._dependency_graph.get_shutdown_order()
        
        if self._logger:
            self._logger.info(f"Stopping components in order: {shutdown_order}")
        
        errors = []
        
        for name in shutdown_order:
            component = await self._registry.get(name)
            
            if component.state not in (LifecycleState.STARTED, LifecycleState.FAILED):
                if self._logger:
                    self._logger.warning(
                        f"Component {name} is not in started/failed state, skipping"
                    )
                continue
            
            try:
                await self._stop_component_internal(component)
            except Exception as e:
                error_msg = f"Failed to stop component {name}: {e}"
                if self._logger:
                    self._logger.error(error_msg)
                errors.append(error_msg)
        
        if errors:
            raise LifecycleError(f"Some components failed to stop: {'; '.join(errors)}")
        
        if self._logger:
            self._logger.info("All components stopped successfully")
    
    async def start_component(self, name: str) -> None:
        """Start a specific component and its dependencies.
        
        Args:
            name: Component name to start
            
        Raises:
            ComponentNotFoundError: If component not found
            LifecycleError: If component or dependencies fail to start
        """
        # Get startup order for this component and its dependencies
        startup_order = await self._dependency_graph.get_startup_order()
        component_index = startup_order.index(name)
        components_to_start = startup_order[:component_index + 1]
        
        # Filter to only components that need starting
        filtered_components = []
        for comp_name in components_to_start:
            component = await self._registry.get(comp_name)
            if component.state == LifecycleState.STOPPED:
                filtered_components.append(comp_name)
        
        if self._logger:
            self._logger.info(
                f"Starting component {name} and dependencies: {filtered_components}"
            )
        
        for comp_name in filtered_components:
            component = await self._registry.get(comp_name)
            await self._start_component_internal(component)
    
    async def stop_component(self, name: str) -> None:
        """Stop a specific component and its dependents.
        
        Args:
            name: Component name to stop
            
        Raises:
            ComponentNotFoundError: If component not found
            LifecycleError: If component or dependents fail to stop
        """
        # Get shutdown order for this component and its dependents
        shutdown_order = await self._dependency_graph.get_shutdown_order()
        component_index = shutdown_order.index(name)
        components_to_stop = shutdown_order[:component_index + 1]
        
        # Filter to only components that need stopping
        filtered_components = []
        for comp_name in components_to_stop:
            component = await self._registry.get(comp_name)
            if component.state in (LifecycleState.STARTED, LifecycleState.FAILED):
                filtered_components.append(comp_name)
        
        if self._logger:
            self._logger.info(
                f"Stopping component {name} and dependents: {filtered_components}"
            )
        
        errors = []
        for comp_name in filtered_components:
            component = await self._registry.get(comp_name)
            try:
                await self._stop_component_internal(component)
            except Exception as e:
                error_msg = f"Failed to stop component {comp_name}: {e}"
                if self._logger:
                    self._logger.error(error_msg)
                errors.append(error_msg)
        
        if errors:
            raise LifecycleError(f"Some components failed to stop: {'; '.join(errors)}")
    
    async def _start_component_internal(self, component) -> None:
        """Internal method to start a single component."""
        if self._logger:
            self._logger.info(f"Starting component: {component.name}")
        
        try:
            await component._state_machine.transition_to(LifecycleState.STARTING)
            await component._state_machine.start_timing()
            
            if isinstance(component, Startable):
                await asyncio.wait_for(component.start(), timeout=self.startup_timeout)
            
            await component._state_machine.transition_to(LifecycleState.STARTED)
            await component._state_machine.end_startup_timing()
            
            if self._logger:
                startup_time = component.get_startup_time()
                self._logger.info(
                    f"Started component: {component.name} "
                    f"(took {startup_time:.2f}s)" if startup_time else ""
                )
        
        except asyncio.TimeoutError:
            await component._state_machine.transition_to(LifecycleState.FAILED)
            raise LifecycleTimeoutError(
                f"Component {component.name} startup timed out after {self.startup_timeout}s"
            )
        except Exception as e:
            await component._state_machine.transition_to(LifecycleState.FAILED)
            raise ComponentStartupFailedError(
                f"Component {component.name} failed to start"
            ) from e
    
    async def _stop_component_internal(self, component) -> None:
        """Internal method to stop a single component."""
        if self._logger:
            self._logger.info(f"Stopping component: {component.name}")
        
        try:
            await component._state_machine.transition_to(LifecycleState.STOPPING)
            await component._state_machine.start_shutdown_timing()
            
            if isinstance(component, Stoppable):
                await asyncio.wait_for(component.stop(), timeout=self.shutdown_timeout)
            
            await component._state_machine.transition_to(LifecycleState.STOPPED)
            await component._state_machine.end_shutdown_timing()
            
            if self._logger:
                shutdown_time = component.get_shutdown_time()
                self._logger.info(
                    f"Stopped component: {component.name} "
                    f"(took {shutdown_time:.2f}s)" if shutdown_time else ""
                )
        
        except asyncio.TimeoutError:
            await component._state_machine.transition_to(LifecycleState.FAILED)
            raise LifecycleTimeoutError(
                f"Component {component.name} shutdown timed out after {self.shutdown_timeout}s"
            )
        except Exception as e:
            await component._state_machine.transition_to(LifecycleState.FAILED)
            raise ComponentShutdownFailedError(
                f"Component {component.name} failed to stop"
            ) from e
```

#### Step 5.2: Create Provider Component

**File: `app/joyride/injection/lifecycle/provider_component.py`**

```python
"""Provider wrapper component implementation."""

import asyncio
from typing import Any, Optional

from ..providers import ProviderBase, ProviderRegistry
from .component import LifecycleComponent
from .enums import LifecycleState, HealthStatus
from .health_converters import HealthConverterRegistry
from .protocols import LoggerProvider


class ProviderComponent(LifecycleComponent):
    """Lifecycle component that wraps a provider."""
    
    def __init__(
        self,
        name: str,
        provider: ProviderBase,
        registry: ProviderRegistry,
        logger: Optional[LoggerProvider] = None
    ):
        """Initialize provider component.
        
        Args:
            name: Component name
            provider: Provider to wrap
            registry: Provider registry for dependency resolution
            logger: Optional logger instance
        """
        super().__init__(name, logger)
        self.provider = provider
        self.registry = registry
        self.instance: Optional[Any] = None
        self._health_converter = HealthConverterRegistry()
    
    async def start(self) -> None:
        """Start the provider component."""
        if self.state != LifecycleState.STOPPED:
            raise RuntimeError(f"Component {self.name} is not in stopped state")
        
        await self._state_machine.transition_to(LifecycleState.STARTING)
        
        try:
            # Create instance through provider
            self.instance = self.provider.create(self.registry)
            
            # Call start method if instance has one
            if hasattr(self.instance, "start") and callable(
                getattr(self.instance, "start")
            ):
                if asyncio.iscoroutinefunction(self.instance.start):
                    await self.instance.start()
                else:
                    self.instance.start()
            
            await self._state_machine.transition_to(LifecycleState.STARTED)
        
        except Exception as e:
            await self._state_machine.transition_to(LifecycleState.FAILED)
            raise RuntimeError(f"Failed to start component {self.name}: {e}") from e
    
    async def stop(self) -> None:
        """Stop the provider component."""
        if self.state not in (LifecycleState.STARTED, LifecycleState.FAILED):
            return  # Already stopped or stopping
        
        await self._state_machine.transition_to(LifecycleState.STOPPING)
        
        try:
            # Call stop method if instance has one
            if (
                self.instance
                and hasattr(self.instance, "stop")
                and callable(getattr(self.instance, "stop"))
            ):
                if asyncio.iscoroutinefunction(self.instance.stop):
                    await self.instance.stop()
                else:
                    self.instance.stop()
            
            await self._state_machine.transition_to(LifecycleState.STOPPED)
            self.instance = None
        
        except Exception as e:
            await self._state_machine.transition_to(LifecycleState.FAILED)
            raise RuntimeError(f"Failed to stop component {self.name}: {e}") from e
    
    async def health_check(self) -> HealthStatus:
        """Perform health check on the provider component."""
        if self.state != LifecycleState.STARTED:
            return await super().health_check()
        
        # Call health check method if instance has one
        if self.instance and hasattr(self.instance, "health_check"):
            try:
                if asyncio.iscoroutinefunction(self.instance.health_check):
                    raw_status = await self.instance.health_check()
                else:
                    raw_status = self.instance.health_check()
                
                return self._health_converter.convert(raw_status)
            
            except Exception as e:
                if self._logger:
                    self._logger.warning(
                        f"Health check failed for component {self.name}: {e}"
                    )
                return HealthStatus.UNHEALTHY
        
        # Default to healthy if no health check method
        return HealthStatus.HEALTHY
```

#### Step 5.3: Create Package Init File

**File: `app/joyride/injection/lifecycle/__init__.py`**

```python
"""Lifecycle management package for the Joyride DNS Service.

This package provides a comprehensive lifecycle management system with:
- Component registration and dependency management
- Startup/shutdown orchestration with dependency ordering
- Health monitoring and status reporting
- Pluggable health status conversion
- Thread-safe state management
"""

# Core enums and exceptions
from .enums import LifecycleState, HealthStatus
from .exceptions import (
    LifecycleError,
    LifecycleDependencyError,
    LifecycleTimeoutError,
    ComponentNotFoundError,
    ComponentAlreadyRegisteredError,
    InvalidStateTransitionError,
    ComponentStartupFailedError,
    ComponentShutdownFailedError,
    CircularDependencyError,
)

# Protocol interfaces
from .protocols import (
    Startable,
    Stoppable,
    HealthCheckable,
    TimingTrackable,
    DependencyAware,
    LoggerProvider,
)

# Core component classes
from .component import BaseComponent, LifecycleComponent

# Service classes
from .component_registry import ComponentRegistry
from .dependency_graph import DependencyGraph
from .health_monitor import HealthMonitor
from .lifecycle_orchestrator import LifecycleOrchestrator

# Specialized components
from .provider_component import ProviderComponent

# Health status conversion
from .health_converters import (
    HealthStatusConverter,
    BooleanHealthConverter,
    StringHealthConverter,
    HealthStatusEnumConverter,
    HealthConverterRegistry,
)

# Validation utilities
from .validators import ComponentValidator, StateTransitionValidator

# State management
from .state_machine import ComponentStateMachine

__all__ = [
    # Enums
    "LifecycleState",
    "HealthStatus",
    
    # Exceptions
    "LifecycleError",
    "LifecycleDependencyError", 
    "LifecycleTimeoutError",
    "ComponentNotFoundError",
    "ComponentAlreadyRegisteredError",
    "InvalidStateTransitionError",
    "ComponentStartupFailedError",
    "ComponentShutdownFailedError",
    "CircularDependencyError",
    
    # Protocols
    "Startable",
    "Stoppable",
    "HealthCheckable",
    "TimingTrackable",
    "DependencyAware",
    "LoggerProvider",
    
    # Components
    "BaseComponent",
    "LifecycleComponent",
    "ProviderComponent",
    
    # Services
    "ComponentRegistry",
    "DependencyGraph",
    "HealthMonitor",
    "LifecycleOrchestrator",
    
    # Health conversion
    "HealthStatusConverter",
    "BooleanHealthConverter",
    "StringHealthConverter", 
    "HealthStatusEnumConverter",
    "HealthConverterRegistry",
    
    # Utilities
    "ComponentValidator",
    "StateTransitionValidator",
    "ComponentStateMachine",
]


# Convenience factory function
def create_lifecycle_manager(
    startup_timeout: float = 30.0,
    shutdown_timeout: float = 30.0,
    health_check_interval: float = 30.0,
    logger: Optional[LoggerProvider] = None
) -> tuple[ComponentRegistry, DependencyGraph, HealthMonitor, LifecycleOrchestrator]:
    """Create a complete lifecycle management system.
    
    Args:
        startup_timeout: Maximum time to wait for component startup
        shutdown_timeout: Maximum time to wait for component shutdown
        health_check_interval: Health check interval in seconds
        logger: Optional logger instance
        
    Returns:
        Tuple of (registry, dependency_graph, health_monitor, orchestrator)
    """
    registry = ComponentRegistry(logger)
    dependency_graph = DependencyGraph(registry, logger)
    health_monitor = HealthMonitor(registry, health_check_interval, logger)
    orchestrator = LifecycleOrchestrator(
        registry, dependency_graph, health_monitor,
        startup_timeout, shutdown_timeout, logger
    )
    
    return registry, dependency_graph, health_monitor, orchestrator
```

### Phase 6: Update Original Module

#### Step 6.1: Create Backward Compatibility Layer

**File: `app/joyride/injection/lifecycle.py` (Updated)**

```python
"""
Component lifecycle management for the Joyride DNS Service.

DEPRECATED: This module is deprecated in favor of the lifecycle package.
Import from app.joyride.injection.lifecycle instead.

This module provides backward compatibility during the transition period.
"""

import warnings
from typing import *

# Import everything from the new package
from .lifecycle import *

# Issue deprecation warning
warnings.warn(
    "Importing from app.joyride.injection.lifecycle module is deprecated. "
    "Use 'from app.joyride.injection.lifecycle import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Backward compatibility aliases
LifecycleManager = LifecycleOrchestrator

def create_lifecycle_manager_legacy(
    startup_timeout: float = 30.0,
    shutdown_timeout: float = 30.0
) -> LifecycleOrchestrator:
    """Legacy function to create lifecycle manager."""
    registry, dependency_graph, health_monitor, orchestrator = create_lifecycle_manager(
        startup_timeout=startup_timeout,
        shutdown_timeout=shutdown_timeout
    )
    return orchestrator
```

### Phase 7: Testing Strategy

#### Step 7.1: Create Test Files

```bash
# Create test directory structure
mkdir -p tests/lifecycle
touch tests/lifecycle/__init__.py
touch tests/lifecycle/test_component.py
touch tests/lifecycle/test_component_registry.py
touch tests/lifecycle/test_dependency_graph.py
touch tests/lifecycle/test_health_monitor.py
touch tests/lifecycle/test_lifecycle_orchestrator.py
touch tests/lifecycle/test_provider_component.py
touch tests/lifecycle/test_validators.py
touch tests/lifecycle/test_state_machine.py
touch tests/lifecycle/test_health_converters.py
touch tests/lifecycle/test_integration.py
```

#### Step 7.2: Update Existing Tests

1. Update import statements in existing lifecycle tests
2. Add tests for new components and interfaces
3. Create integration tests for complete workflows
4. Add performance benchmarks for concurrent operations

### Phase 8: Migration and Cleanup

#### Step 8.1: Update Import Statements

Update all files that import from the old lifecycle module:

```python
# Old imports
from app.joyride.injection.lifecycle import LifecycleManager

# New imports  
from app.joyride.injection.lifecycle import LifecycleOrchestrator
# or
from app.joyride.injection.lifecycle import create_lifecycle_manager
```

#### Step 8.2: Gradual Migration

1. **Week 1**: Create new package structure and basic components
2. **Week 2**: Implement service layer (registry, dependency graph)
3. **Week 3**: Add health monitoring and orchestrator
4. **Week 4**: Update provider component and create backward compatibility
5. **Week 5**: Update all import statements and test integration
6. **Week 6**: Remove deprecated module after thorough testing

## Verification Steps

### After Each Phase

1. **Run Tests**: `make test` - All existing tests should pass
2. **Run Linting**: `make lint` - No new linting errors
3. **Type Checking**: `uv run mypy app/joyride/injection/lifecycle/` 
4. **Import Testing**: Verify all imports work correctly

### Final Verification

1. **Performance Testing**: Benchmark startup/shutdown times
2. **Memory Usage**: Check for memory leaks in lifecycle operations  
3. **Concurrency Testing**: Test with multiple components and dependencies
4. **Integration Testing**: Full application startup/shutdown cycles

## Benefits of This Approach

1. **Single Responsibility**: Each class has one clear purpose
2. **Testability**: Small, focused classes are easier to test
3. **Extensibility**: New health converters and component types without code changes
4. **Type Safety**: Comprehensive type hints and protocol definitions
5. **Maintainability**: Clear separation of concerns and well-defined interfaces
6. **Backward Compatibility**: Existing code continues to work during migration

## Post-Migration Cleanup

After successful migration and testing:

1. Remove the old `lifecycle.py` file
2. Remove backward compatibility warnings
3. Update documentation to reference new package structure
4. Consider additional optimizations and features

This comprehensive refactoring will transform the monolithic lifecycle module into a well-structured, maintainable, and extensible package that follows SOLID principles and Python best practices.
