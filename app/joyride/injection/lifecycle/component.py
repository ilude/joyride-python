"""
Component lifecycle management for Joyride.

Provides base classes for components with lifecycle management, dependency
injection, and health checking capabilities.
"""
import asyncio
import logging
import time
from enum import Enum
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)


class ComponentState(Enum):
    """Component lifecycle states."""

    CREATED = "created"
    STARTING = "starting"
    STARTED = "started"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class ComponentError(Exception):
    """Base exception for component errors."""

    pass


class ComponentStateError(ComponentError):
    """Raised when invalid state transitions are attempted."""

    pass


class ComponentStartupError(ComponentError):
    """Raised when component startup fails."""

    pass


class ComponentShutdownError(ComponentError):
    """Raised when component shutdown fails."""

    pass


class Component:
    """
    Base component class with dependency management and state tracking.

    Components can declare dependencies on other components and will be
    started/stopped in the correct order based on dependency graph.
    """

    def __init__(self, name: str):
        """Initialize component with given name."""
        self.name = name
        self.state = ComponentState.CREATED
        self.dependencies: Set[str] = set()
        self._dependents: Set[str] = set()
        self._metadata: Dict[str, Any] = {}
        self._start_time: Optional[float] = None
        self._stop_time: Optional[float] = None

    def add_dependency(self, dependency_name: str) -> None:
        """Add a dependency on another component."""
        if self.state != ComponentState.CREATED:
            raise ComponentStateError(
                f"Cannot add dependencies to component {self.name} in state {self.state.value}"
            )
        self.dependencies.add(dependency_name)

    def add_dependent(self, dependent_name: str) -> None:
        """Add a component that depends on this one."""
        self._dependents.add(dependent_name)

    def get_dependencies(self) -> Set[str]:
        """Get all component dependencies."""
        return self.dependencies.copy()

    def get_dependents(self) -> Set[str]:
        """Get all components that depend on this one."""
        return self._dependents.copy()

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for the component."""
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata for the component."""
        return self._metadata.get(key, default)

    def get_startup_time(self) -> Optional[float]:
        """Get time taken to start the component in seconds."""
        return self._start_time

    def get_shutdown_time(self) -> Optional[float]:
        """Get time taken to stop the component in seconds."""
        return self._stop_time

    def is_created(self) -> bool:
        """Check if component is in CREATED state."""
        return self.state == ComponentState.CREATED

    def is_starting(self) -> bool:
        """Check if component is in STARTING state."""
        return self.state == ComponentState.STARTING

    def is_started(self) -> bool:
        """Check if component is in STARTED state."""
        return self.state == ComponentState.STARTED

    def is_stopping(self) -> bool:
        """Check if component is in STOPPING state."""
        return self.state == ComponentState.STOPPING

    def is_stopped(self) -> bool:
        """Check if component is in STOPPED state."""
        return self.state == ComponentState.STOPPED

    def is_failed(self) -> bool:
        """Check if component is in FAILED state."""
        return self.state == ComponentState.FAILED

    def __repr__(self) -> str:
        """String representation of component."""
        return f"Component(name='{self.name}', state={self.state.value})"


class StartableComponent(Component):
    """
    Component with start/stop lifecycle management.

    Provides async start() and stop() methods with state validation
    and timing metrics. Subclasses implement _do_start() and _do_stop()
    for custom startup/shutdown logic.
    """

    async def start(self) -> None:
        """
        Start the component.

        Validates state transition and calls _do_start() for custom logic.
        Records timing metrics for startup duration.
        """
        if self.state not in (ComponentState.CREATED, ComponentState.STOPPED):
            raise ComponentStateError(
                f"Cannot start component {self.name} from state {self.state.value}"
            )

        logger.info(f"Starting component: {self.name}")
        self.state = ComponentState.STARTING

        start_time = time.time()
        try:
            await self._do_start()
            end_time = time.time()
            self._start_time = end_time - start_time
            self.state = ComponentState.STARTED
            logger.info(f"Component {self.name} started in {self._start_time:.3f}s")
        except Exception as e:
            self.state = ComponentState.FAILED
            logger.error(f"Failed to start component {self.name}: {e}")
            raise ComponentStartupError(f"Failed to start {self.name}: {e}") from e

    async def stop(self) -> None:
        """
        Stop the component.

        Validates state transition and calls _do_stop() for custom logic.
        Records timing metrics for shutdown duration.
        """
        if self.state not in (ComponentState.STARTED, ComponentState.FAILED):
            raise ComponentStateError(
                f"Cannot stop component {self.name} from state {self.state.value}"
            )

        logger.info(f"Stopping component: {self.name}")
        self.state = ComponentState.STOPPING

        start_time = time.time()
        try:
            await self._do_stop()
            end_time = time.time()
            self._stop_time = end_time - start_time
            self.state = ComponentState.STOPPED
            logger.info(f"Component {self.name} stopped in {self._stop_time:.3f}s")
        except Exception as e:
            self.state = ComponentState.FAILED
            logger.error(f"Failed to stop component {self.name}: {e}")
            raise ComponentShutdownError(f"Failed to stop {self.name}: {e}") from e

    async def _do_start(self) -> None:
        """
        Custom start logic to be implemented by subclasses.

        This method is called during start() and should contain
        the actual startup logic for the component.
        """
        pass

    async def _do_stop(self) -> None:
        """
        Custom stop logic to be implemented by subclasses.

        This method is called during stop() and should contain
        the actual shutdown logic for the component.
        """
        pass


class HealthCheckableComponent(StartableComponent):
    """
    Component with health checking capabilities.

    Provides health check functionality to monitor component status
    and detect failures. Health checks can be used by monitoring
    systems and dependency managers.
    """

    def __init__(self, name: str):
        """Initialize health checkable component."""
        super().__init__(name)
        self._last_health_check: Optional[float] = None
        self._health_check_interval = 30.0  # seconds
        self._health_check_timeout = 5.0  # seconds

    async def health_check(self) -> bool:
        """
        Perform health check on the component.

        Returns True if component is healthy, False otherwise.
        Updates last health check timestamp.
        """
        if not self.is_started():
            return False

        self._last_health_check = time.time()

        try:
            # Use timeout to prevent hanging health checks
            return await asyncio.wait_for(
                self._do_health_check(), timeout=self._health_check_timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Health check timeout for component {self.name}")
            return False
        except Exception as e:
            logger.error(f"Health check failed for component {self.name}: {e}")
            return False

    async def _do_health_check(self) -> bool:
        """
        Custom health check logic to be implemented by subclasses.

        This method should return True if the component is healthy,
        False otherwise. It should not raise exceptions.
        """
        return True

    def get_last_health_check(self) -> Optional[float]:
        """Get timestamp of last health check."""
        return self._last_health_check

    def set_health_check_interval(self, interval: float) -> None:
        """Set health check interval in seconds."""
        self._health_check_interval = interval

    def get_health_check_interval(self) -> float:
        """Get health check interval in seconds."""
        return self._health_check_interval

    def set_health_check_timeout(self, timeout: float) -> None:
        """Set health check timeout in seconds."""
        self._health_check_timeout = timeout

    def get_health_check_timeout(self) -> float:
        """Get health check timeout in seconds."""
        return self._health_check_timeout
