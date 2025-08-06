# Simplified Lifecycle Refactoring Procedure

## Overview

This document provides a simplified, step-by-step procedure for refactoring the `lifecycle.py` module using a **real implementation first** approach. Each step produces working code with passing tests, avoiding throwaway mocks and focusing on code quality.

## Core Principles

1. **Real Implementation First**: Build actual working components, not mocks
2. **Test After Each Step**: `make test` must pass after every step
3. **Minimal Mocking**: Use real objects and minimal interfaces
4. **Incremental Value**: Each step adds working functionality
5. **Simple Dependencies**: Start with the simplest components first

## Simplified Target Structure

```
app/joyride/injection/lifecycle/
├── __init__.py                 # Public API exports
├── types.py                   # Enums, exceptions, and simple types
├── interfaces.py              # Minimal protocol definitions
├── component.py               # Base component implementation
├── registry.py                # Component registration
├── orchestrator.py            # Startup/shutdown coordination
├── health.py                  # Health monitoring
└── provider_adapter.py        # Provider integration
```

## Implementation Steps

### ✅ Step 1: Foundation Types and Interfaces (30 minutes) - COMPLETED

**Goal**: Create the basic types and minimal interfaces needed.

#### 1.1 Create Directory and Types

```bash
mkdir -p app/joyride/injection/lifecycle
```

**File: `app/joyride/injection/lifecycle/types.py`**

```python
"""Core types for lifecycle management."""

from enum import Enum
from typing import Protocol, Optional, Set, Any


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
```

**File: `app/joyride/injection/lifecycle/interfaces.py`**

```python
"""Minimal protocol interfaces."""

from typing import Protocol, Optional
from .types import HealthStatus


class Startable(Protocol):
    """Protocol for startable components."""
    async def start(self) -> None: ...


class Stoppable(Protocol):
    """Protocol for stoppable components."""
    async def stop(self) -> None: ...


class HealthCheckable(Protocol):
    """Protocol for health checkable components."""
    async def health_check(self) -> HealthStatus: ...


class Logger(Protocol):
    """Simple logger protocol."""
    def info(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
    def debug(self, message: str) -> None: ...
```

#### 1.2 Create Basic Test

**File: `tests/lifecycle/test_types.py`**

```python
"""Test lifecycle types."""

import pytest
from app.joyride.injection.lifecycle.types import (
    LifecycleState,
    HealthStatus,
    validate_transition,
    InvalidStateTransitionError,
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
```

**Run Test**: `make test` should pass

#### 1.3 Mark Step Complete
If `make test` passes successfully, update this document to mark Step 1 as completed by changing `⬜ Step 1` to `✅ Step 1` and adding "- COMPLETED" to the title.

### ⬜ Step 2: Simple Component Implementation (45 minutes)

**Goal**: Create a working component class that can be used immediately.

**File: `app/joyride/injection/lifecycle/component.py`**

```python
"""Base component implementation."""

import asyncio
import time
from typing import Set, Optional
from .types import LifecycleState, HealthStatus, validate_transition
from .interfaces import Startable, Stoppable, HealthCheckable, Logger


class Component:
    """Base lifecycle component with real functionality."""
    
    def __init__(self, name: str, logger: Optional[Logger] = None):
        self.name = name
        self._state = LifecycleState.STOPPED
        self._dependencies: Set[str] = set()
        self._dependents: Set[str] = set()
        self._startup_time: Optional[float] = None
        self._shutdown_time: Optional[float] = None
        self._logger = logger
        self._state_lock = asyncio.Lock()
    
    @property
    def state(self) -> LifecycleState:
        """Get current state."""
        return self._state
    
    async def _transition_to(self, new_state: LifecycleState) -> None:
        """Transition to new state with validation."""
        async with self._state_lock:
            validate_transition(self._state, new_state)
            old_state = self._state
            self._state = new_state
            
            if self._logger:
                self._logger.debug(f"{self.name}: {old_state.value} -> {new_state.value}")
    
    def add_dependency(self, component_name: str) -> None:
        """Add dependency."""
        self._dependencies.add(component_name)
    
    def add_dependent(self, component_name: str) -> None:
        """Add dependent."""
        self._dependents.add(component_name)
    
    @property
    def dependencies(self) -> Set[str]:
        """Get dependencies."""
        return self._dependencies.copy()
    
    @property
    def dependents(self) -> Set[str]:
        """Get dependents."""
        return self._dependents.copy()
    
    def get_startup_time(self) -> Optional[float]:
        """Get startup time."""
        return self._startup_time
    
    def get_shutdown_time(self) -> Optional[float]:
        """Get shutdown time."""
        return self._shutdown_time


class StartableComponent(Component):
    """Component that can be started and stopped."""
    
    async def start(self) -> None:
        """Start the component."""
        if self._state != LifecycleState.STOPPED:
            raise RuntimeError(f"Component {self.name} is not stopped")
        
        await self._transition_to(LifecycleState.STARTING)
        
        start_time = time.time()
        try:
            await self._do_start()
            await self._transition_to(LifecycleState.STARTED)
            self._startup_time = time.time() - start_time
            
            if self._logger:
                self._logger.info(f"Started {self.name} in {self._startup_time:.2f}s")
        
        except Exception as e:
            await self._transition_to(LifecycleState.FAILED)
            if self._logger:
                self._logger.error(f"Failed to start {self.name}: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the component."""
        if self._state not in (LifecycleState.STARTED, LifecycleState.FAILED):
            return  # Already stopped
        
        await self._transition_to(LifecycleState.STOPPING)
        
        start_time = time.time()
        try:
            await self._do_stop()
            await self._transition_to(LifecycleState.STOPPED)
            self._shutdown_time = time.time() - start_time
            
            if self._logger:
                self._logger.info(f"Stopped {self.name} in {self._shutdown_time:.2f}s")
        
        except Exception as e:
            await self._transition_to(LifecycleState.FAILED)
            if self._logger:
                self._logger.error(f"Failed to stop {self.name}: {e}")
            raise
    
    async def _do_start(self) -> None:
        """Override this method to implement start logic."""
        pass
    
    async def _do_stop(self) -> None:
        """Override this method to implement stop logic."""
        pass


class HealthCheckableComponent(StartableComponent):
    """Component with health checking."""
    
    async def health_check(self) -> HealthStatus:
        """Basic health check based on state."""
        if self._state == LifecycleState.STARTED:
            return HealthStatus.HEALTHY
        elif self._state == LifecycleState.FAILED:
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.UNKNOWN
```

**File: `tests/lifecycle/test_component.py`**

```python
"""Test component implementation."""

import pytest
from app.joyride.injection.lifecycle.component import (
    Component,
    StartableComponent,
    HealthCheckableComponent,
)
from app.joyride.injection.lifecycle.types import LifecycleState, HealthStatus


@pytest.mark.asyncio
async def test_component_basic():
    """Test basic component functionality."""
    component = Component("test")
    
    assert component.name == "test"
    assert component.state == LifecycleState.STOPPED
    assert len(component.dependencies) == 0
    assert len(component.dependents) == 0


@pytest.mark.asyncio
async def test_component_dependencies():
    """Test dependency management."""
    component = Component("test")
    
    component.add_dependency("dep1")
    component.add_dependency("dep2")
    component.add_dependent("child1")
    
    assert "dep1" in component.dependencies
    assert "dep2" in component.dependencies
    assert "child1" in component.dependents


@pytest.mark.asyncio
async def test_startable_component():
    """Test startable component lifecycle."""
    component = StartableComponent("test")
    
    # Start component
    await component.start()
    assert component.state == LifecycleState.STARTED
    assert component.get_startup_time() is not None
    
    # Stop component
    await component.stop()
    assert component.state == LifecycleState.STOPPED
    assert component.get_shutdown_time() is not None


@pytest.mark.asyncio
async def test_health_checkable_component():
    """Test health checking."""
    component = HealthCheckableComponent("test")
    
    # Health check when stopped
    health = await component.health_check()
    assert health == HealthStatus.UNKNOWN
    
    # Start and check health
    await component.start()
    health = await component.health_check()
    assert health == HealthStatus.HEALTHY
    
    # Stop and check
    await component.stop()
    health = await component.health_check()
    assert health == HealthStatus.UNKNOWN


class CustomComponent(StartableComponent):
    """Test component with custom start/stop logic."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.started = False
        self.stopped = False
    
    async def _do_start(self) -> None:
        self.started = True
    
    async def _do_stop(self) -> None:
        self.stopped = True


@pytest.mark.asyncio
async def test_custom_component():
    """Test component with custom logic."""
    component = CustomComponent("custom")
    
    await component.start()
    assert component.started is True
    assert component.state == LifecycleState.STARTED
    
    await component.stop()
    assert component.stopped is True
    assert component.state == LifecycleState.STOPPED
```

**Run Test**: `make test` should pass

#### 2.1 Mark Step Complete
If `make test` passes successfully, update this document to mark Step 2 as completed by changing `⬜ Step 2` to `✅ Step 2` and adding "- COMPLETED" to the title.

### ⬜ Step 3: Component Registry (30 minutes)

**Goal**: Create a working registry for managing components.

**File: `app/joyride/injection/lifecycle/registry.py`**

```python
"""Component registry implementation."""

import asyncio
from typing import Dict, List, Optional
from .component import Component
from .types import ComponentNotFoundError, LifecycleState
from .interfaces import Logger


class ComponentRegistry:
    """Registry for managing components."""
    
    def __init__(self, logger: Optional[Logger] = None):
        self._components: Dict[str, Component] = {}
        self._lock = asyncio.Lock()
        self._logger = logger
    
    async def register(self, component: Component) -> None:
        """Register a component."""
        async with self._lock:
            if component.name in self._components:
                raise ValueError(f"Component {component.name} already registered")
            
            self._components[component.name] = component
            
            if self._logger:
                self._logger.info(f"Registered component: {component.name}")
    
    async def unregister(self, name: str) -> None:
        """Unregister a component."""
        async with self._lock:
            if name not in self._components:
                raise ComponentNotFoundError(f"Component {name} not found")
            
            component = self._components[name]
            if component.state not in (LifecycleState.STOPPED, LifecycleState.FAILED):
                raise ValueError(f"Component {name} must be stopped before unregistering")
            
            del self._components[name]
            
            if self._logger:
                self._logger.info(f"Unregistered component: {name}")
    
    async def get(self, name: str) -> Component:
        """Get a component by name."""
        async with self._lock:
            if name not in self._components:
                raise ComponentNotFoundError(f"Component {name} not found")
            return self._components[name]
    
    async def get_optional(self, name: str) -> Optional[Component]:
        """Get component or None if not found."""
        async with self._lock:
            return self._components.get(name)
    
    async def list_names(self) -> List[str]:
        """Get all component names."""
        async with self._lock:
            return list(self._components.keys())
    
    async def list_components(self) -> List[Component]:
        """Get all components."""
        async with self._lock:
            return list(self._components.values())
    
    async def count(self) -> int:
        """Get component count."""
        async with self._lock:
            return len(self._components)
```

**File: `tests/lifecycle/test_registry.py`**

```python
"""Test component registry."""

import pytest
from app.joyride.injection.lifecycle.registry import ComponentRegistry
from app.joyride.injection.lifecycle.component import Component, StartableComponent
from app.joyride.injection.lifecycle.types import ComponentNotFoundError


@pytest.mark.asyncio
async def test_registry_basic():
    """Test basic registry operations."""
    registry = ComponentRegistry()
    
    # Empty registry
    assert await registry.count() == 0
    assert await registry.list_names() == []
    
    # Register component
    component = Component("test")
    await registry.register(component)
    
    assert await registry.count() == 1
    assert "test" in await registry.list_names()
    
    # Get component
    retrieved = await registry.get("test")
    assert retrieved is component
    
    # Optional get
    optional = await registry.get_optional("test")
    assert optional is component
    
    none_result = await registry.get_optional("nonexistent")
    assert none_result is None


@pytest.mark.asyncio
async def test_registry_errors():
    """Test registry error conditions."""
    registry = ComponentRegistry()
    
    # Get nonexistent component
    with pytest.raises(ComponentNotFoundError):
        await registry.get("nonexistent")
    
    # Unregister nonexistent component
    with pytest.raises(ComponentNotFoundError):
        await registry.unregister("nonexistent")
    
    # Duplicate registration
    component = Component("test")
    await registry.register(component)
    
    with pytest.raises(ValueError, match="already registered"):
        await registry.register(component)


@pytest.mark.asyncio
async def test_registry_unregister():
    """Test component unregistration."""
    registry = ComponentRegistry()
    component = StartableComponent("test")
    
    await registry.register(component)
    assert await registry.count() == 1
    
    # Cannot unregister started component
    await component.start()
    with pytest.raises(ValueError, match="must be stopped"):
        await registry.unregister("test")
    
    # Can unregister stopped component
    await component.stop()
    await registry.unregister("test")
    assert await registry.count() == 0
```

**Run Test**: `make test` should pass

#### 3.1 Mark Step Complete
If `make test` passes successfully, update this document to mark Step 3 as completed by changing `⬜ Step 3` to `✅ Step 3` and adding "- COMPLETED" to the title.

### ⬜ Step 4: Simple Orchestrator (45 minutes)

**Goal**: Create a working orchestrator that can start/stop components in dependency order.

**File: `app/joyride/injection/lifecycle/orchestrator.py`**

```python
"""Lifecycle orchestrator for startup/shutdown coordination."""

import asyncio
from typing import List, Set, Optional
from .registry import ComponentRegistry
from .component import Component
from .types import LifecycleState, LifecycleError
from .interfaces import Logger, Startable, Stoppable


class LifecycleOrchestrator:
    """Orchestrates component startup and shutdown."""
    
    def __init__(self, registry: ComponentRegistry, logger: Optional[Logger] = None):
        self._registry = registry
        self._logger = logger
    
    async def start_all(self) -> None:
        """Start all components in dependency order."""
        startup_order = await self._get_startup_order()
        
        if self._logger:
            self._logger.info(f"Starting components: {startup_order}")
        
        for name in startup_order:
            component = await self._registry.get(name)
            if hasattr(component, 'start') and component.state == LifecycleState.STOPPED:
                await component.start()
    
    async def stop_all(self) -> None:
        """Stop all components in reverse dependency order."""
        shutdown_order = await self._get_shutdown_order()
        
        if self._logger:
            self._logger.info(f"Stopping components: {shutdown_order}")
        
        errors = []
        for name in shutdown_order:
            try:
                component = await self._registry.get(name)
                if hasattr(component, 'stop') and component.state in (
                    LifecycleState.STARTED, LifecycleState.FAILED
                ):
                    await component.stop()
            except Exception as e:
                error_msg = f"Failed to stop {name}: {e}"
                if self._logger:
                    self._logger.error(error_msg)
                errors.append(error_msg)
        
        if errors:
            raise LifecycleError(f"Some components failed to stop: {'; '.join(errors)}")
    
    async def start_component(self, name: str) -> None:
        """Start a specific component and its dependencies."""
        startup_order = await self._get_startup_order()
        
        # Find components that need to be started
        try:
            target_index = startup_order.index(name)
            components_to_start = startup_order[:target_index + 1]
        except ValueError:
            raise LifecycleError(f"Component {name} not found in startup order")
        
        for comp_name in components_to_start:
            component = await self._registry.get(comp_name)
            if hasattr(component, 'start') and component.state == LifecycleState.STOPPED:
                await component.start()
    
    async def stop_component(self, name: str) -> None:
        """Stop a specific component and its dependents."""
        shutdown_order = await self._get_shutdown_order()
        
        # Find components that need to be stopped
        try:
            target_index = shutdown_order.index(name)
            components_to_stop = shutdown_order[:target_index + 1]
        except ValueError:
            raise LifecycleError(f"Component {name} not found in shutdown order")
        
        for comp_name in components_to_stop:
            component = await self._registry.get(comp_name)
            if hasattr(component, 'stop') and component.state in (
                LifecycleState.STARTED, LifecycleState.FAILED
            ):
                await component.stop()
    
    async def _get_startup_order(self) -> List[str]:
        """Get component startup order using topological sort."""
        components = await self._registry.list_components()
        
        # Simple topological sort
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(component: Component):
            if component.name in temp_visited:
                raise LifecycleError(f"Circular dependency detected: {component.name}")
            if component.name in visited:
                return
            
            temp_visited.add(component.name)
            
            # Visit dependencies first
            for dep_name in component.dependencies:
                # Find dependency component
                for dep_comp in components:
                    if dep_comp.name == dep_name:
                        visit(dep_comp)
                        break
            
            temp_visited.remove(component.name)
            visited.add(component.name)
            order.append(component.name)
        
        # Visit all components
        for component in components:
            if component.name not in visited:
                visit(component)
        
        return order
    
    async def _get_shutdown_order(self) -> List[str]:
        """Get component shutdown order (reverse of startup)."""
        startup_order = await self._get_startup_order()
        return list(reversed(startup_order))
```

**File: `tests/lifecycle/test_orchestrator.py`**

```python
"""Test lifecycle orchestrator."""

import pytest
from app.joyride.injection.lifecycle.orchestrator import LifecycleOrchestrator
from app.joyride.injection.lifecycle.registry import ComponentRegistry
from app.joyride.injection.lifecycle.component import StartableComponent
from app.joyride.injection.lifecycle.types import LifecycleState, LifecycleError


class TestComponent(StartableComponent):
    """Test component with tracking."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.start_count = 0
        self.stop_count = 0
    
    async def _do_start(self) -> None:
        self.start_count += 1
    
    async def _do_stop(self) -> None:
        self.stop_count += 1


@pytest.mark.asyncio
async def test_orchestrator_basic():
    """Test basic orchestrator functionality."""
    registry = ComponentRegistry()
    orchestrator = LifecycleOrchestrator(registry)
    
    # Add components
    comp1 = TestComponent("test1")
    comp2 = TestComponent("test2")
    
    await registry.register(comp1)
    await registry.register(comp2)
    
    # Start all
    await orchestrator.start_all()
    
    assert comp1.state == LifecycleState.STARTED
    assert comp2.state == LifecycleState.STARTED
    assert comp1.start_count == 1
    assert comp2.start_count == 1
    
    # Stop all
    await orchestrator.stop_all()
    
    assert comp1.state == LifecycleState.STOPPED
    assert comp2.state == LifecycleState.STOPPED
    assert comp1.stop_count == 1
    assert comp2.stop_count == 1


@pytest.mark.asyncio
async def test_orchestrator_dependencies():
    """Test dependency ordering."""
    registry = ComponentRegistry()
    orchestrator = LifecycleOrchestrator(registry)
    
    # Create components with dependencies
    comp1 = TestComponent("database")  # No dependencies
    comp2 = TestComponent("api")       # Depends on comp1
    comp3 = TestComponent("web")      # Depends on comp2
    
    comp2.add_dependency("database")
    comp3.add_dependency("api")
    
    await registry.register(comp1)
    await registry.register(comp2)
    await registry.register(comp3)
    
    # Start all - should start in dependency order
    await orchestrator.start_all()
    
    assert comp1.state == LifecycleState.STARTED
    assert comp2.state == LifecycleState.STARTED
    assert comp3.state == LifecycleState.STARTED
    
    # Stop all - should stop in reverse order
    await orchestrator.stop_all()
    
    assert comp1.state == LifecycleState.STOPPED
    assert comp2.state == LifecycleState.STOPPED
    assert comp3.state == LifecycleState.STOPPED


@pytest.mark.asyncio
async def test_orchestrator_circular_dependency():
    """Test circular dependency detection."""
    registry = ComponentRegistry()
    orchestrator = LifecycleOrchestrator(registry)
    
    # Create circular dependency
    comp1 = TestComponent("comp1")
    comp2 = TestComponent("comp2")
    
    comp1.add_dependency("comp2")
    comp2.add_dependency("comp1")  # Circular!
    
    await registry.register(comp1)
    await registry.register(comp2)
    
    # Should detect circular dependency
    with pytest.raises(LifecycleError, match="Circular dependency"):
        await orchestrator.start_all()


@pytest.mark.asyncio
async def test_orchestrator_individual_components():
    """Test starting/stopping individual components."""
    registry = ComponentRegistry()
    orchestrator = LifecycleOrchestrator(registry)
    
    # Create components
    database = TestComponent("database")
    api = TestComponent("api")
    
    api.add_dependency("database")
    
    await registry.register(database)
    await registry.register(api)
    
    # Start database only
    await orchestrator.start_component("database")
    
    assert database.state == LifecycleState.STARTED
    assert api.state == LifecycleState.STOPPED
    
    # Start api (should not start database again)
    await orchestrator.start_component("api")
    
    assert database.state == LifecycleState.STARTED
    assert api.state == LifecycleState.STARTED
    
    # Stop api only
    await orchestrator.stop_component("api")
    
    assert database.state == LifecycleState.STARTED
    assert api.state == LifecycleState.STOPPED
```

**Run Test**: `make test` should pass

#### 4.1 Mark Step Complete
If `make test` passes successfully, update this document to mark Step 4 as completed by changing `⬜ Step 4` to `✅ Step 4` and adding "- COMPLETED" to the title.

### ⬜ Step 5: Simple Health Monitor (30 minutes)

**Goal**: Create a basic health monitoring system.

**File: `app/joyride/injection/lifecycle/health.py`**

```python
"""Health monitoring for components."""

import asyncio
from typing import Dict, List, Optional
from .registry import ComponentRegistry
from .types import HealthStatus
from .interfaces import Logger, HealthCheckable


class HealthMonitor:
    """Monitors component health."""
    
    def __init__(
        self,
        registry: ComponentRegistry,
        check_interval: float = 30.0,
        logger: Optional[Logger] = None
    ):
        self._registry = registry
        self._check_interval = check_interval
        self._logger = logger
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    async def start_monitoring(self) -> None:
        """Start periodic health monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            return
        
        self._shutdown_event.clear()
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        
        if self._logger:
            self._logger.info("Started health monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
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
            self._logger.info("Stopped health monitoring")
    
    async def check_all(self) -> Dict[str, HealthStatus]:
        """Check health of all components."""
        results = {}
        components = await self._registry.list_components()
        
        for component in components:
            try:
                if hasattr(component, 'health_check'):
                    results[component.name] = await component.health_check()
                else:
                    results[component.name] = HealthStatus.UNKNOWN
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Health check failed for {component.name}: {e}")
                results[component.name] = HealthStatus.UNHEALTHY
        
        return results
    
    async def check_component(self, name: str) -> HealthStatus:
        """Check health of specific component."""
        component = await self._registry.get(name)
        
        try:
            if hasattr(component, 'health_check'):
                return await component.health_check()
            else:
                return HealthStatus.UNKNOWN
        except Exception as e:
            if self._logger:
                self._logger.warning(f"Health check failed for {name}: {e}")
            return HealthStatus.UNHEALTHY
    
    async def get_unhealthy_components(self) -> List[str]:
        """Get list of unhealthy component names."""
        health_results = await self.check_all()
        return [
            name for name, status in health_results.items()
            if status == HealthStatus.UNHEALTHY
        ]
    
    async def _monitor_loop(self) -> None:
        """Periodic health monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(), timeout=self._check_interval
                )
                break  # Shutdown requested
            except asyncio.TimeoutError:
                pass  # Timeout reached, do health check
            
            try:
                unhealthy = await self.get_unhealthy_components()
                if unhealthy and self._logger:
                    self._logger.warning(f"Unhealthy components: {unhealthy}")
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Health monitoring error: {e}")
```

**File: `tests/lifecycle/test_health.py`**

```python
"""Test health monitoring."""

import asyncio
import pytest
from app.joyride.injection.lifecycle.health import HealthMonitor
from app.joyride.injection.lifecycle.registry import ComponentRegistry
from app.joyride.injection.lifecycle.component import HealthCheckableComponent
from app.joyride.injection.lifecycle.types import HealthStatus


class TestHealthComponent(HealthCheckableComponent):
    """Component for integration testing."""
    
    def __init__(self, name: str, health: HealthStatus = HealthStatus.HEALTHY):
        super().__init__(name)
        self._health = health
        self.start_count = 0
        self.stop_count = 0
    
    async def _do_start(self) -> None:
        self.start_count += 1
    
    async def _do_stop(self) -> None:
        self.stop_count += 1
    
    async def health_check(self) -> HealthStatus:
        if self.state == LifecycleState.STARTED:
            return self._health
        return await super().health_check()
    
    def set_health(self, health: HealthStatus) -> None:
        self._health = health


@pytest.mark.asyncio
async def test_health_monitor_basic():
    """Test basic health monitoring."""
    registry = ComponentRegistry()
    monitor = HealthMonitor(registry, check_interval=0.1)
    
    # Add healthy component
    comp1 = TestHealthComponent("comp1", HealthStatus.HEALTHY)
    await registry.register(comp1)
    
    # Check health
    health_results = await monitor.check_all()
    assert health_results["comp1"] == HealthStatus.HEALTHY
    
    # Check individual component
    individual_health = await monitor.check_component("comp1")
    assert individual_health == HealthStatus.HEALTHY
    
    # Check unhealthy components
    unhealthy = await monitor.get_unhealthy_components()
    assert len(unhealthy) == 0


@pytest.mark.asyncio
async def test_health_monitor_unhealthy():
    """Test monitoring unhealthy components."""
    registry = ComponentRegistry()
    monitor = HealthMonitor(registry)
    
    # Add unhealthy component
    comp1 = TestHealthComponent("comp1", HealthStatus.UNHEALTHY)
    await registry.register(comp1)
    
    # Check health
    health_results = await monitor.check_all()
    assert health_results["comp1"] == HealthStatus.UNHEALTHY
    
    # Check unhealthy list
    unhealthy = await monitor.get_unhealthy_components()
    assert "comp1" in unhealthy


@pytest.mark.asyncio
async def test_health_monitor_periodic():
    """Test periodic health monitoring."""
    registry = ComponentRegistry()
    monitor = HealthMonitor(registry, check_interval=0.05)  # Very short interval
    
    comp1 = TestHealthComponent("comp1", HealthStatus.HEALTHY)
    await registry.register(comp1)
    
    # Start monitoring
    await monitor.start_monitoring()
    
    # Let it run for a bit
    await asyncio.sleep(0.1)
    
    # Change health status
    comp1.set_health(HealthStatus.UNHEALTHY)
    
    # Let it check again
    await asyncio.sleep(0.1)
    
    # Stop monitoring
    await monitor.stop_monitoring()
    
    # Verify final state
    health = await monitor.check_component("comp1")
    assert health == HealthStatus.UNHEALTHY


class FailingHealthComponent(HealthCheckableComponent):
    """Component that fails health checks."""
    
    async def health_check(self) -> HealthStatus:
        raise RuntimeError("Health check failed")


@pytest.mark.asyncio
async def test_health_monitor_exceptions():
    """Test health monitoring with exceptions."""
    registry = ComponentRegistry()
    monitor = HealthMonitor(registry)
    
    comp1 = FailingHealthComponent("comp1")
    await registry.register(comp1)
    
    # Should handle exceptions gracefully
    health_results = await monitor.check_all()
    assert health_results["comp1"] == HealthStatus.UNHEALTHY
    
    individual_health = await monitor.check_component("comp1")
    assert individual_health == HealthStatus.UNHEALTHY
```

**Run Test**: `make test` should pass

#### 5.1 Mark Step Complete
If `make test` passes successfully, update this document to mark Step 5 as completed by changing `⬜ Step 5` to `✅ Step 5` and adding "- COMPLETED" to the title.

### ⬜ Step 6: Provider Integration (30 minutes)

**Goal**: Integrate with existing provider system.

**File: `app/joyride/injection/lifecycle/provider_adapter.py`**

```python
"""Adapter for integrating providers with lifecycle system."""

import asyncio
from typing import Any, Optional
from ..providers import ProviderBase, ProviderRegistry
from .component import HealthCheckableComponent
from .types import HealthStatus
from .interfaces import Logger


class ProviderComponent(HealthCheckableComponent):
    """Lifecycle component that wraps a provider."""
    
    def __init__(
        self,
        name: str,
        provider: ProviderBase,
        provider_registry: ProviderRegistry,
        logger: Optional[Logger] = None
    ):
        super().__init__(name, logger)
        self._provider = provider
        self._provider_registry = provider_registry
        self.instance: Optional[Any] = None
    
    async def _do_start(self) -> None:
        """Start the provider."""
        # Create instance through provider
        self.instance = self._provider.create(self._provider_registry)
        
        # Call start method if it exists
        if hasattr(self.instance, "start"):
            if asyncio.iscoroutinefunction(self.instance.start):
                await self.instance.start()
            else:
                self.instance.start()
    
    async def _do_stop(self) -> None:
        """Stop the provider."""
        # Call stop method if it exists
        if self.instance and hasattr(self.instance, "stop"):
            if asyncio.iscoroutinefunction(self.instance.stop):
                await self.instance.stop()
            else:
                self.instance.stop()
        
        self.instance = None
    
    async def health_check(self) -> HealthStatus:
        """Check provider health."""
        # Use parent health check if not started
        if not self.instance:
            return await super().health_check()
        
        # Call provider health check if available
        if hasattr(self.instance, "health_check"):
            try:
                if asyncio.iscoroutinefunction(self.instance.health_check):
                    result = await self.instance.health_check()
                else:
                    result = self.instance.health_check()
                
                # Convert result to HealthStatus
                return self._convert_health_status(result)
            
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Health check failed for {self.name}: {e}")
                return HealthStatus.UNHEALTHY
        
        # Default to healthy if no health check method
        return HealthStatus.HEALTHY
    
    def _convert_health_status(self, result: Any) -> HealthStatus:
        """Convert health check result to HealthStatus."""
        if isinstance(result, HealthStatus):
            return result
        elif isinstance(result, bool):
            return HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
        elif isinstance(result, str):
            mapping = {
                "healthy": HealthStatus.HEALTHY,
                "degraded": HealthStatus.DEGRADED,
                "unhealthy": HealthStatus.UNHEALTHY,
                "ok": HealthStatus.HEALTHY,
                "good": HealthStatus.HEALTHY,
                "bad": HealthStatus.UNHEALTHY,
                "error": HealthStatus.UNHEALTHY,
            }
            return mapping.get(result.lower(), HealthStatus.UNKNOWN)
        else:
            return HealthStatus.UNKNOWN
```

**File: `tests/lifecycle/test_provider_adapter.py`**

```python
"""Test provider adapter."""

import pytest
from app.joyride.injection.lifecycle.provider_adapter import ProviderComponent
from app.joyride.injection.lifecycle.types import LifecycleState, HealthStatus
from app.joyride.injection.providers import ProviderBase, ProviderRegistry


class MockInstance:
    """Mock instance for testing."""
    
    def __init__(self):
        self.started = False
        self.stopped = False
        self.health_result = True
    
    def start(self):
        self.started = True
    
    def stop(self):
        self.stopped = True
    
    def health_check(self):
        return self.health_result


class MockProvider(ProviderBase):
    """Mock provider for testing."""
    
    def create(self, registry: ProviderRegistry) -> MockInstance:
        return MockInstance()


@pytest.mark.asyncio
async def test_provider_component_basic():
    """Test basic provider component functionality."""
    provider = MockProvider()
    registry = ProviderRegistry()
    
    component = ProviderComponent("test", provider, registry)
    
    assert component.instance is None
    assert component.state == LifecycleState.STOPPED
    
    # Start component
    await component.start()
    
    assert component.instance is not None
    assert component.instance.started is True
    assert component.state == LifecycleState.STARTED
    
    # Stop component
    await component.stop()
    
    assert component.instance is None
    assert component.state == LifecycleState.STOPPED


@pytest.mark.asyncio
async def test_provider_component_health():
    """Test provider component health checking."""
    provider = MockProvider()
    registry = ProviderRegistry()
    
    component = ProviderComponent("test", provider, registry)
    
    # Health check when stopped
    health = await component.health_check()
    assert health == HealthStatus.UNKNOWN
    
    # Start and check health
    await component.start()
    health = await component.health_check()
    assert health == HealthStatus.HEALTHY
    
    # Change instance health
    component.instance.health_result = False
    health = await component.health_check()
    assert health == HealthStatus.UNHEALTHY
    
    # Test string health results
    component.instance.health_result = "healthy"
    health = await component.health_check()
    assert health == HealthStatus.HEALTHY
    
    component.instance.health_result = "unhealthy"
    health = await component.health_check()
    assert health == HealthStatus.UNHEALTHY


class MockInstanceNoMethods:
    """Mock instance without start/stop/health methods."""
    pass


class MockProviderNoMethods(ProviderBase):
    """Mock provider that creates instance without methods."""
    
    def create(self, registry: ProviderRegistry) -> MockInstanceNoMethods:
        return MockInstanceNoMethods()


@pytest.mark.asyncio
async def test_provider_component_no_methods():
    """Test provider component with instance that has no special methods."""
    provider = MockProviderNoMethods()
    registry = ProviderRegistry()
    
    component = ProviderComponent("test", provider, registry)
    
    # Should work fine without start/stop methods
    await component.start()
    assert component.instance is not None
    assert component.state == LifecycleState.STARTED
    
    # Health should default to healthy
    health = await component.health_check()
    assert health == HealthStatus.HEALTHY
    
    await component.stop()
    assert component.instance is None
    assert component.state == LifecycleState.STOPPED
```

**Run Test**: `make test` should pass

#### 6.1 Mark Step Complete
If `make test` passes successfully, update this document to mark Step 6 as completed by changing `⬜ Step 6` to `✅ Step 6` and adding "- COMPLETED" to the title.

### ⬜ Step 7: Package Integration (15 minutes)

**Goal**: Create the public API and integrate everything.

**File: `app/joyride/injection/lifecycle/__init__.py`**

```python
"""Lifecycle management package for Joyride DNS Service."""

# Core types
from .types import (
    LifecycleState,
    HealthStatus,
    LifecycleError,
    ComponentNotFoundError,
    InvalidStateTransitionError,
)

# Interfaces
from .interfaces import (
    Startable,
    Stoppable,
    HealthCheckable,
    Logger,
)

# Components
from .component import (
    Component,
    StartableComponent,
    HealthCheckableComponent,
)

# Services
from .registry import ComponentRegistry
from .orchestrator import LifecycleOrchestrator
from .health import HealthMonitor

# Provider integration
from .provider_adapter import ProviderComponent

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
```

**File: `tests/lifecycle/test_integration.py`**

```python
"""Integration tests for complete lifecycle system."""

import pytest
from app.joyride.injection.lifecycle import (
    create_lifecycle_system,
    StartableComponent,
    HealthCheckableComponent,
    LifecycleState,
    HealthStatus,
)


class IntegrationTestComponent(HealthCheckableComponent):
    """Component for integration testing."""
    
    def __init__(self, name: str, health: HealthStatus = HealthStatus.HEALTHY):
        super().__init__(name)
        self._health = health
        self.start_count = 0
        self.stop_count = 0
    
    async def _do_start(self) -> None:
        self.start_count += 1
    
    async def _do_stop(self) -> None:
        self.stop_count += 1
    
    async def health_check(self) -> HealthStatus:
        if self.state == LifecycleState.STARTED:
            return self._health
        return await super().health_check()
    
    def set_health(self, health: HealthStatus) -> None:
        self._health = health


@pytest.mark.asyncio
async def test_complete_lifecycle_system():
    """Test complete lifecycle system integration."""
    # Create system
    registry, orchestrator, health_monitor = create_lifecycle_system()
    
    # Create components with dependencies
    comp1 = IntegrationTestComponent("database")
    comp2 = IntegrationTestComponent("api")
    comp3 = IntegrationTestComponent("web")
    
    # Set up dependencies: web -> api -> database
    comp2.add_dependency("database")
    comp3.add_dependency("api")
    
    # Register components
    await registry.register(comp1)
    await registry.register(comp2)
    await registry.register(comp3)
    
    # Start health monitoring
    await health_monitor.start_monitoring()
    
    # Start all components
    await orchestrator.start_all()
    
    # Verify all started
    assert comp1.state == LifecycleState.STARTED
    assert comp2.state == LifecycleState.STARTED
    assert comp3.state == LifecycleState.STARTED
    
    # Check health
    health_results = await health_monitor.check_all()
    assert health_results["database"] == HealthStatus.HEALTHY
    assert health_results["api"] == HealthStatus.HEALTHY
    assert health_results["web"] == HealthStatus.HEALTHY
    
    # Simulate health issue
    comp2.set_health(HealthStatus.UNHEALTHY)
    
    unhealthy = await health_monitor.get_unhealthy_components()
    assert "api" in unhealthy
    
    # Stop all
    await orchestrator.stop_all()
    
    # Stop monitoring
    await health_monitor.stop_monitoring()
    
    # Verify all stopped
    assert comp1.state == LifecycleState.STOPPED
    assert comp2.state == LifecycleState.STOPPED
    assert comp3.state == LifecycleState.STOPPED


@pytest.mark.asyncio
async def test_partial_component_management():
    """Test starting/stopping individual components."""
    registry, orchestrator, health_monitor = create_lifecycle_system()
    
    # Create components
    database = IntegrationTestComponent("database")
    api = IntegrationTestComponent("api")
    
    api.add_dependency("database")
    
    await registry.register(database)
    await registry.register(api)
    
    # Start database only
    await orchestrator.start_component("database")
    
    assert database.state == LifecycleState.STARTED
    assert api.state == LifecycleState.STOPPED
    
    # Start api (should not start database again)
    await orchestrator.start_component("api")
    
    assert database.state == LifecycleState.STARTED
    assert api.state == LifecycleState.STARTED
    
    # Stop api only
    await orchestrator.stop_component("api")
    
    assert database.state == LifecycleState.STARTED
    assert api.state == LifecycleState.STOPPED


@pytest.mark.asyncio 
async def test_system_resilience():
    """Test system handles failures gracefully."""
    registry, orchestrator, health_monitor = create_lifecycle_system()
    
    # Component that fails to start
    class FailingComponent(StartableComponent):
        async def _do_start(self) -> None:
            raise RuntimeError("Startup failed")
    
    failing_comp = FailingComponent("failing")
    good_comp = IntegrationTestComponent("good")
    
    await registry.register(failing_comp)
    await registry.register(good_comp)
    
    # Start all - should handle failure gracefully
    with pytest.raises(RuntimeError, match="Startup failed"):
        await orchestrator.start_all()
    
    # Failing component should be in failed state
    assert failing_comp.state == LifecycleState.FAILED
    
    # Good component should still be started
    assert good_comp.state == LifecycleState.STARTED
    
    # Can still stop good component
    await orchestrator.stop_component("good")
    assert good_comp.state == LifecycleState.STOPPED
```

**Run Test**: `make test` should pass

#### 7.1 Mark Step Complete
If `make test` passes successfully, update this document to mark Step 7 as completed by changing `⬜ Step 7` to `✅ Step 7` and adding "- COMPLETED" to the title.

### ⬜ Step 8: Backward Compatibility (15 minutes)

**Goal**: Update the original lifecycle.py to use the new system.

**File: `app/joyride/injection/lifecycle.py` (Update existing)**

```python
"""
DEPRECATED: Import from app.joyride.injection.lifecycle package instead.

This module provides backward compatibility during migration.
"""

import warnings
from typing import Optional

# Import from new package
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


def create_legacy_lifecycle_manager(
    startup_timeout: float = 30.0,
    shutdown_timeout: float = 30.0,
    logger: Optional[Logger] = None
) -> LifecycleOrchestrator:
    """Legacy function to create lifecycle manager."""
    registry, orchestrator, health_monitor = create_lifecycle_system(logger)
    return orchestrator
```

#### 8.1 Mark Step Complete
If `make test` passes successfully, update this document to mark Step 8 as completed by changing `⬜ Step 8` to `✅ Step 8` and adding "- COMPLETED" to the title.

### ⬜ Step 9: Final Testing (15 minutes)

**Goal**: Ensure everything works together and all tests pass.

**Create comprehensive test**:

```bash
# Run all tests
make test

# Run specific lifecycle tests
uv run pytest tests/lifecycle/ -v

# Check coverage
uv run pytest tests/lifecycle/ --cov=app.joyride.injection.lifecycle --cov-report=term-missing
```

**File: `tests/lifecycle/test_backward_compatibility.py`**

```python
"""Test backward compatibility."""

import warnings
import pytest


def test_backward_compatibility_import():
    """Test importing from old module still works."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Import from old location
        from app.joyride.injection.lifecycle import LifecycleManager
        
        # Should have issued deprecation warning
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message)
        
        # Should still work
        assert LifecycleManager is not None


def test_legacy_factory_function():
    """Test legacy factory function."""
    from app.joyride.injection.lifecycle import create_legacy_lifecycle_manager
    
    manager = create_legacy_lifecycle_manager()
    assert manager is not None
```

#### 9.1 Mark Step Complete
If `make test` passes successfully, update this document to mark Step 9 as completed by changing `⬜ Step 9` to `✅ Step 9` and adding "- COMPLETED" to the title.

## Summary

This simplified approach provides:

1. **Working Code at Each Step**: Every step produces functional, testable code
2. **Minimal Mocking**: Uses real implementations and simple test components
3. **Incremental Development**: Each step builds on the previous
4. **Test-Driven**: `make test` passes after each step
5. **Simple Structure**: Focused on essential functionality first
6. **Backward Compatibility**: Existing code continues to work

**Total Time Estimate**: 4-5 hours for complete implementation

**Key Benefits**:
- Real components that can be used immediately
- Simple dependency structure
- Comprehensive test coverage
- No throwaway code
- Clear separation of concerns
- Easy to understand and maintain

The refactored system maintains all the functionality of the original while being much simpler to test, maintain, and extend.
