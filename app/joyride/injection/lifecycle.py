"""Component lifecycle management for the Joyride DNS Service.

This module provides lifecycle management capabilities including:
- Component startup and shutdown ordering
- Graceful shutdown handling
- Health check monitoring
- Dependency-aware lifecycle coordination
"""

import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .providers import ProviderBase, ProviderRegistry


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


class LifecycleComponent(ABC):
    """Abstract base class for lifecycle-managed components."""

    def __init__(self, name: str):
        """Initialize lifecycle component.

        Args:
            name: Component name
        """
        if not name or not isinstance(name, str):
            raise ValueError("Component name must be a non-empty string")

        self.name = name
        self.state = LifecycleState.STOPPED
        self.health_status = HealthStatus.UNKNOWN
        self.dependencies: Set[str] = set()
        self.dependents: Set[str] = set()
        self._startup_time: Optional[float] = None
        self._shutdown_time: Optional[float] = None
        self._last_health_check: Optional[float] = None
        self._lock = threading.Lock()

    @abstractmethod
    async def start(self) -> None:
        """Start the component.

        Raises:
            Exception: If component fails to start
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the component gracefully.

        Raises:
            Exception: If component fails to stop gracefully
        """
        pass

    async def health_check(self) -> HealthStatus:
        """Perform health check on the component.

        Returns:
            Component health status
        """
        # Default implementation - override in subclasses
        with self._lock:
            if self.state == LifecycleState.STARTED:
                return HealthStatus.HEALTHY
            elif self.state == LifecycleState.FAILED:
                return HealthStatus.UNHEALTHY
            else:
                return HealthStatus.UNKNOWN

    def add_dependency(self, component_name: str) -> None:
        """Add a dependency on another component.

        Args:
            component_name: Name of the component this depends on
        """
        if not component_name or not isinstance(component_name, str):
            raise ValueError("Dependency name must be a non-empty string")

        with self._lock:
            self.dependencies.add(component_name)

    def add_dependent(self, component_name: str) -> None:
        """Add a component that depends on this one.

        Args:
            component_name: Name of the component that depends on this
        """
        if not component_name or not isinstance(component_name, str):
            raise ValueError("Dependent name must be a non-empty string")

        with self._lock:
            self.dependents.add(component_name)

    def get_startup_time(self) -> Optional[float]:
        """Get component startup duration in seconds."""
        return self._startup_time

    def get_shutdown_time(self) -> Optional[float]:
        """Get component shutdown duration in seconds."""
        return self._shutdown_time

    def get_last_health_check_time(self) -> Optional[float]:
        """Get timestamp of last health check."""
        return self._last_health_check

    def __str__(self) -> str:
        """String representation of component."""
        return f"{self.__class__.__name__}({self.name}, state={self.state.value})"

    def __repr__(self) -> str:
        """Developer representation of component."""
        return (
            f"{self.__class__.__name__}(name={self.name!r}, "
            f"state={self.state.value}, health={self.health_status.value})"
        )


class ProviderComponent(LifecycleComponent):
    """Lifecycle component that wraps a provider."""

    def __init__(
        self, name: str, provider: ProviderBase, registry: ProviderRegistry
    ):
        """Initialize provider component.

        Args:
            name: Component name
            provider: Provider to wrap
            registry: Provider registry for dependency resolution
        """
        super().__init__(name)
        self.provider = provider
        self.registry = registry
        self.instance: Optional[Any] = None

    async def start(self) -> None:
        """Start the provider component."""
        start_time = time.time()

        try:
            with self._lock:
                if self.state != LifecycleState.STOPPED:
                    raise RuntimeError(f"Component {self.name} is not in stopped state")

                self.state = LifecycleState.STARTING

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

            with self._lock:
                self.state = LifecycleState.STARTED
                self.health_status = HealthStatus.HEALTHY
                self._startup_time = time.time() - start_time

        except Exception as e:
            with self._lock:
                self.state = LifecycleState.FAILED
                self.health_status = HealthStatus.UNHEALTHY
                self._startup_time = time.time() - start_time
            raise RuntimeError(f"Failed to start component {self.name}: {e}") from e

    async def stop(self) -> None:
        """Stop the provider component."""
        stop_time = time.time()

        try:
            with self._lock:
                if self.state not in (
                    LifecycleState.STARTED,
                    LifecycleState.FAILED,
                ):
                    return  # Already stopped or stopping

                self.state = LifecycleState.STOPPING

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

            with self._lock:
                self.state = LifecycleState.STOPPED
                self.health_status = HealthStatus.UNKNOWN
                self._shutdown_time = time.time() - stop_time
                self.instance = None

        except Exception as e:
            with self._lock:
                self.state = LifecycleState.FAILED
                self.health_status = HealthStatus.UNHEALTHY
                self._shutdown_time = time.time() - stop_time
            raise RuntimeError(f"Failed to stop component {self.name}: {e}") from e

    async def health_check(self) -> HealthStatus:
        """Perform health check on the provider component."""
        with self._lock:
            self._last_health_check = time.time()

            if self.state != LifecycleState.STARTED:
                return await super().health_check()

            # Call health check method if instance has one
            if self.instance and hasattr(self.instance, "health_check"):
                try:
                    if asyncio.iscoroutinefunction(self.instance.health_check):
                        status = await self.instance.health_check()
                    else:
                        status = self.instance.health_check()

                    if isinstance(status, HealthStatus):
                        self.health_status = status
                        return status
                    elif isinstance(status, bool):
                        self.health_status = (
                            HealthStatus.HEALTHY
                            if status
                            else HealthStatus.UNHEALTHY
                        )
                        return self.health_status
                    elif isinstance(status, str):
                        # Try to map string to health status
                        status_mapping = {
                            "healthy": HealthStatus.HEALTHY,
                            "degraded": HealthStatus.DEGRADED,
                            "unhealthy": HealthStatus.UNHEALTHY,
                            "unknown": HealthStatus.UNKNOWN,
                        }
                        self.health_status = status_mapping.get(
                            status.lower(), HealthStatus.UNKNOWN
                        )
                        return self.health_status

                except Exception as e:
                    logging.warning(
                        f"Health check failed for component {self.name}: {e}"
                    )
                    self.health_status = HealthStatus.UNHEALTHY
                    return self.health_status

            # Default to healthy if no health check method
            self.health_status = HealthStatus.HEALTHY
            return self.health_status


class LifecycleError(Exception):
    """Base exception for lifecycle management errors."""

    pass


class LifecycleDependencyError(LifecycleError):
    """Exception raised when there are dependency issues."""

    pass


class LifecycleTimeoutError(LifecycleError):
    """Exception raised when lifecycle operations timeout."""

    pass


class LifecycleManager:
    """Manages component lifecycle with dependency ordering."""

    def __init__(self, startup_timeout: float = 30.0, shutdown_timeout: float = 30.0):
        """Initialize lifecycle manager.

        Args:
            startup_timeout: Maximum time to wait for component startup
            shutdown_timeout: Maximum time to wait for component shutdown
        """
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        self.components: Dict[str, LifecycleComponent] = {}
        self._logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._health_check_interval = 30.0  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    def register_component(self, component: LifecycleComponent) -> None:
        """Register a component for lifecycle management.

        Args:
            component: Component to register

        Raises:
            ValueError: If component name already registered
        """
        if not isinstance(component, LifecycleComponent):
            raise ValueError("Component must be a LifecycleComponent")

        with self._lock:
            if component.name in self.components:
                raise ValueError(f"Component '{component.name}' is already registered")

            self.components[component.name] = component
            self._logger.info(f"Registered component: {component.name}")

    def unregister_component(self, name: str) -> None:
        """Unregister a component.

        Args:
            name: Component name to unregister

        Raises:
            ValueError: If component not found
        """
        with self._lock:
            if name not in self.components:
                raise ValueError(f"Component '{name}' is not registered")

            component = self.components[name]
            if component.state not in (
                LifecycleState.STOPPED,
                LifecycleState.FAILED,
            ):
                raise ValueError(
                    f"Component '{name}' must be stopped before unregistering"
                )

            del self.components[name]
            self._logger.info(f"Unregistered component: {name}")

    def add_dependency(self, component_name: str, dependency_name: str) -> None:
        """Add a dependency between components.

        Args:
            component_name: Name of component that depends on dependency
            dependency_name: Name of dependency component

        Raises:
            ValueError: If components not found or circular dependency detected
        """
        with self._lock:
            if component_name not in self.components:
                raise ValueError(f"Component '{component_name}' not found")
            if dependency_name not in self.components:
                raise ValueError(f"Dependency '{dependency_name}' not found")

            # Check for circular dependencies
            if self._has_circular_dependency(component_name, dependency_name):
                raise LifecycleDependencyError(
                    f"Adding dependency would create circular dependency: {component_name} -> {dependency_name}"
                )

            self.components[component_name].add_dependency(dependency_name)
            self.components[dependency_name].add_dependent(component_name)

            self._logger.info(
                f"Added dependency: {component_name} depends on {dependency_name}"
            )

    def _has_circular_dependency(
        self, component_name: str, new_dependency: str
    ) -> bool:
        """Check if adding a dependency would create a circular dependency.

        Args:
            component_name: Component that would depend on new_dependency
            new_dependency: New dependency to check

        Returns:
            True if circular dependency would be created
        """
        # Check if new_dependency already depends on component_name (directly or indirectly)
        visited = set()

        def check_path(current: str, target: str) -> bool:
            if current == target:
                return True
            if current in visited:
                return False

            visited.add(current)

            current_component = self.components.get(current)
            if current_component:
                for dep in current_component.dependencies:
                    if check_path(dep, target):
                        return True

            return False

        return check_path(new_dependency, component_name)

    def get_startup_order(self) -> List[str]:
        """Get component startup order based on dependencies.

        Returns:
            List of component names in startup order

        Raises:
            LifecycleDependencyError: If circular dependencies exist
        """
        with self._lock:
            # Topological sort for startup order
            visited = set()
            temp_visited = set()
            order = []

            def visit(name: str):
                if name in temp_visited:
                    raise LifecycleDependencyError(
                        f"Circular dependency detected involving {name}"
                    )
                if name in visited:
                    return

                temp_visited.add(name)
                component = self.components[name]

                # Visit dependencies first
                for dep_name in component.dependencies:
                    visit(dep_name)

                temp_visited.remove(name)
                visited.add(name)
                order.append(name)

            # Visit all components
            for name in self.components:
                if name not in visited:
                    visit(name)

            return order

    def get_shutdown_order(self) -> List[str]:
        """Get component shutdown order (reverse of startup order).

        Returns:
            List of component names in shutdown order
        """
        return list(reversed(self.get_startup_order()))

    async def start_all(self) -> None:
        """Start all components in dependency order.

        Raises:
            LifecycleError: If any component fails to start
        """
        startup_order = self.get_startup_order()
        self._logger.info(f"Starting components in order: {startup_order}")

        for name in startup_order:
            component = self.components[name]

            if component.state != LifecycleState.STOPPED:
                self._logger.warning(
                    f"Component {name} is not in stopped state, skipping"
                )
                continue

            self._logger.info(f"Starting component: {name}")

            try:
                # Start component with timeout
                await asyncio.wait_for(component.start(), timeout=self.startup_timeout)
                self._logger.info(
                    f"Started component: {name} (took {component.get_startup_time():.2f}s)"
                )

            except asyncio.TimeoutError:
                raise LifecycleTimeoutError(
                    f"Component {name} startup timed out after {self.startup_timeout}s"
                )
            except Exception as e:
                self._logger.error(f"Failed to start component {name}: {e}")
                raise LifecycleError(f"Component {name} failed to start") from e

        # Start health check monitoring
        await self._start_health_monitoring()

        self._logger.info("All components started successfully")

    async def stop_all(self) -> None:
        """Stop all components in reverse dependency order.

        Raises:
            LifecycleError: If any component fails to stop
        """
        # Stop health monitoring
        await self._stop_health_monitoring()

        shutdown_order = self.get_shutdown_order()
        self._logger.info(f"Stopping components in order: {shutdown_order}")

        errors = []

        for name in shutdown_order:
            component = self.components[name]

            if component.state not in (
                LifecycleState.STARTED,
                LifecycleState.FAILED,
            ):
                self._logger.warning(
                    f"Component {name} is not in started/failed state, skipping"
                )
                continue

            self._logger.info(f"Stopping component: {name}")

            try:
                # Stop component with timeout
                await asyncio.wait_for(component.stop(), timeout=self.shutdown_timeout)
                self._logger.info(
                    f"Stopped component: {name} (took {component.get_shutdown_time():.2f}s)"
                )

            except asyncio.TimeoutError:
                error_msg = f"Component {name} shutdown timed out after {self.shutdown_timeout}s"
                self._logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Failed to stop component {name}: {e}"
                self._logger.error(error_msg)
                errors.append(error_msg)

        if errors:
            raise LifecycleError(
                f"Some components failed to stop: {'; '.join(errors)}"
            )

        self._logger.info("All components stopped successfully")

    async def start_component(self, name: str) -> None:
        """Start a specific component and its dependencies.

        Args:
            name: Component name to start

        Raises:
            ValueError: If component not found
            LifecycleError: If component or dependencies fail to start
        """
        if name not in self.components:
            raise ValueError(f"Component '{name}' not found")

        # Get startup order for this component and its dependencies
        startup_order = self.get_startup_order()
        component_index = startup_order.index(name)
        components_to_start = startup_order[: component_index + 1]

        # Filter to only components that need starting
        components_to_start = [
            comp_name
            for comp_name in components_to_start
            if self.components[comp_name].state == LifecycleState.STOPPED
        ]

        self._logger.info(
            f"Starting component {name} and dependencies: {components_to_start}"
        )

        for comp_name in components_to_start:
            component = self.components[comp_name]
            self._logger.info(f"Starting component: {comp_name}")

            try:
                await asyncio.wait_for(component.start(), timeout=self.startup_timeout)
                self._logger.info(f"Started component: {comp_name}")
            except Exception as e:
                raise LifecycleError(
                    f"Failed to start component {comp_name}"
                ) from e

    async def stop_component(self, name: str) -> None:
        """Stop a specific component and its dependents.

        Args:
            name: Component name to stop

        Raises:
            ValueError: If component not found
            LifecycleError: If component or dependents fail to stop
        """
        if name not in self.components:
            raise ValueError(f"Component '{name}' not found")

        # Get shutdown order for this component and its dependents
        shutdown_order = self.get_shutdown_order()
        component_index = shutdown_order.index(name)
        components_to_stop = shutdown_order[: component_index + 1]

        # Filter to only components that need stopping
        components_to_stop = [
            comp_name
            for comp_name in components_to_stop
            if self.components[comp_name].state
            in (LifecycleState.STARTED, LifecycleState.FAILED)
        ]

        self._logger.info(
            f"Stopping component {name} and dependents: {components_to_stop}"
        )

        errors = []
        for comp_name in components_to_stop:
            component = self.components[comp_name]
            self._logger.info(f"Stopping component: {comp_name}")

            try:
                await asyncio.wait_for(component.stop(), timeout=self.shutdown_timeout)
                self._logger.info(f"Stopped component: {comp_name}")
            except Exception as e:
                error_msg = f"Failed to stop component {comp_name}: {e}"
                self._logger.error(error_msg)
                errors.append(error_msg)

        if errors:
            raise LifecycleError(
                f"Some components failed to stop: {'; '.join(errors)}"
            )

    async def health_check_all(self) -> Dict[str, HealthStatus]:
        """Perform health check on all components.

        Returns:
            Dictionary mapping component names to their health status
        """
        results = {}

        with self._lock:
            components = list(self.components.items())

        for name, component in components:
            try:
                status = await component.health_check()
                results[name] = status
            except Exception as e:
                self._logger.warning(f"Health check failed for component {name}: {e}")
                results[name] = HealthStatus.UNHEALTHY

        return results

    def get_component_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all components.

        Returns:
            Dictionary with component status information
        """
        status = {}

        with self._lock:
            for name, component in self.components.items():
                status[name] = {
                    "state": component.state.value,
                    "health_status": component.health_status.value,
                    "dependencies": list(component.dependencies),
                    "dependents": list(component.dependents),
                    "startup_time": component.get_startup_time(),
                    "shutdown_time": component.get_shutdown_time(),
                    "last_health_check": component.get_last_health_check_time(),
                }

        return status

    async def _start_health_monitoring(self) -> None:
        """Start periodic health check monitoring."""
        if self._health_check_task and not self._health_check_task.done():
            return  # Already running

        self._shutdown_event.clear()
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._logger.info("Started health check monitoring")

    async def _stop_health_monitoring(self) -> None:
        """Stop periodic health check monitoring."""
        self._shutdown_event.set()

        if self._health_check_task and not self._health_check_task.done():
            try:
                await asyncio.wait_for(self._health_check_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

        self._logger.info("Stopped health check monitoring")

    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        while not self._shutdown_event.is_set():
            try:
                # Wait for either shutdown event or interval timeout
                await asyncio.wait_for(
                    self._shutdown_event.wait(), timeout=self._health_check_interval
                )
                break  # Shutdown event was set
            except asyncio.TimeoutError:
                pass  # Timeout reached, perform health checks

            try:
                health_results = await self.health_check_all()

                # Log unhealthy components
                unhealthy = [
                    name
                    for name, status in health_results.items()
                    if status == HealthStatus.UNHEALTHY
                ]

                if unhealthy:
                    self._logger.warning(f"Unhealthy components detected: {unhealthy}")

            except Exception as e:
                self._logger.error(f"Error during health check monitoring: {e}")

    def set_health_check_interval(self, interval: float) -> None:
        """Set health check interval.

        Args:
            interval: Health check interval in seconds
        """
        if interval <= 0:
            raise ValueError("Health check interval must be positive")

        self._health_check_interval = interval
        self._logger.info(f"Health check interval set to {interval}s")

    def get_health_check_interval(self) -> float:
        """Get current health check interval."""
        return self._health_check_interval
