"""Tests for Joyride Lifecycle Management System

This module tests component lifecycle management including startup/shutdown ordering,
graceful shutdown handling, and health check monitoring.
"""

import asyncio

import pytest

from app.joyride.injection.lifecycle import (
    HealthStatus,
    LifecycleComponent,
    LifecycleDependencyError,
    LifecycleError,
    LifecycleManager,
    LifecycleState,
    LifecycleTimeoutError,
    ProviderComponent,
)
from app.joyride.injection.providers import ProviderBase, ProviderRegistry


class MockComponent(LifecycleComponent):
    """Mock component for testing."""

    def __init__(
        self,
        name: str,
        start_delay: float = 0.0,
        stop_delay: float = 0.0,
        start_should_fail: bool = False,
        stop_should_fail: bool = False,
    ):
        super().__init__(name)
        self.start_delay = start_delay
        self.stop_delay = stop_delay
        self.start_should_fail = start_should_fail
        self.stop_should_fail = stop_should_fail
        self.start_called = False
        self.stop_called = False
        self.health_check_called = False
        self._startup_time = None
        self._shutdown_time = None

    async def start(self) -> None:
        """Mock start implementation."""
        import time

        start_time = time.time()

        self.start_called = True
        self.state = LifecycleState.STARTING

        if self.start_delay > 0:
            await asyncio.sleep(self.start_delay)

        if self.start_should_fail:
            self.state = LifecycleState.FAILED
            self.health_status = HealthStatus.UNHEALTHY
            raise RuntimeError(f"Mock start failure for {self.name}")

        self.state = LifecycleState.STARTED
        self.health_status = HealthStatus.HEALTHY
        self._startup_time = time.time() - start_time

    async def stop(self) -> None:
        """Mock stop implementation."""
        import time

        start_time = time.time()

        self.stop_called = True
        self.state = LifecycleState.STOPPING

        if self.stop_delay > 0:
            await asyncio.sleep(self.stop_delay)

        if self.stop_should_fail:
            self.state = LifecycleState.FAILED
            raise RuntimeError(f"Mock stop failure for {self.name}")

        self.state = LifecycleState.STOPPED
        self.health_status = HealthStatus.UNKNOWN
        self._shutdown_time = time.time() - start_time

    async def health_check(self) -> HealthStatus:
        """Mock health check implementation."""
        self.health_check_called = True
        if self.state == LifecycleState.STARTED:
            return HealthStatus.HEALTHY
        elif self.state == LifecycleState.FAILED:
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.UNKNOWN

    def get_startup_time(self):
        """Get startup time."""
        return self._startup_time

    def get_shutdown_time(self):
        """Get shutdown time."""
        return self._shutdown_time


class MockProvider(ProviderBase):
    """Mock provider for testing."""

    def __init__(self, name: str, create_func=None):
        super().__init__(name)
        self.create_func = create_func or (lambda registry: MockService(name))
        self.create_called = False
        self.can_create_called = False

    def create(self, registry):
        """Mock create implementation."""
        self.create_called = True
        return self.create_func(registry)

    def can_create(self, registry) -> bool:
        """Mock can_create implementation."""
        self.can_create_called = True
        return True

    def get_dependencies(self):
        """Mock get_dependencies implementation."""
        return []


class MockService:
    """Mock service for testing provider components."""

    def __init__(
        self, name: str, has_lifecycle: bool = False, has_health_check: bool = False
    ):
        self.name = name
        self.has_lifecycle = has_lifecycle
        self.has_health_check = has_health_check
        self.started = False
        self.stopped = False
        self.health_status = True

        # Dynamically add lifecycle methods if enabled
        if has_lifecycle:
            self.start = self._start
            self.stop = self._stop

        if has_health_check:
            self.health_check = self._health_check

    async def _start(self) -> None:
        """Mock start method."""
        self.started = True

    async def _stop(self) -> None:
        """Mock stop method."""
        self.stopped = True

    async def _health_check(self) -> bool:
        """Mock health check method."""
        return self.health_status


class TestLifecycleComponent:
    """Test LifecycleComponent functionality."""

    def test_component_creation(self):
        """Test creating a lifecycle component."""
        component = MockComponent("test_component")

        assert component.name == "test_component"
        assert component.state == LifecycleState.STOPPED
        assert component.health_status == HealthStatus.UNKNOWN
        assert component.dependencies == set()
        assert component.dependents == set()
        assert component.get_startup_time() is None
        assert component.get_shutdown_time() is None
        assert component.get_last_health_check_time() is None

    def test_component_validation(self):
        """Test component validation."""
        # Invalid name
        with pytest.raises(
            ValueError, match="Component name must be a non-empty string"
        ):
            MockComponent("")

        with pytest.raises(
            ValueError, match="Component name must be a non-empty string"
        ):
            MockComponent(None)

    def test_add_dependency(self):
        """Test adding dependencies."""
        component = MockComponent("test_component")

        component.add_dependency("dependency1")
        component.add_dependency("dependency2")

        assert "dependency1" in component.dependencies
        assert "dependency2" in component.dependencies

        # Invalid dependency
        with pytest.raises(
            ValueError, match="Dependency name must be a non-empty string"
        ):
            component.add_dependency("")

    def test_add_dependent(self):
        """Test adding dependents."""
        component = MockComponent("test_component")

        component.add_dependent("dependent1")
        component.add_dependent("dependent2")

        assert "dependent1" in component.dependents
        assert "dependent2" in component.dependents

        # Invalid dependent
        with pytest.raises(
            ValueError, match="Dependent name must be a non-empty string"
        ):
            component.add_dependent("")

    @pytest.mark.asyncio
    async def test_component_lifecycle(self):
        """Test component lifecycle states."""
        component = MockComponent("test_component")

        # Initial state
        assert component.state == LifecycleState.STOPPED

        # Start component
        await component.start()
        assert component.start_called

        # Stop component
        await component.stop()
        assert component.stop_called

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality."""
        component = MockComponent("test_component")

        # Default health check
        status = await component.health_check()
        assert status == HealthStatus.UNKNOWN
        assert component.health_check_called

    def test_string_representation(self):
        """Test string representations."""
        component = MockComponent("test_component")

        str_repr = str(component)
        assert "MockComponent" in str_repr
        assert "test_component" in str_repr
        assert "stopped" in str_repr

        repr_str = repr(component)
        assert "MockComponent" in repr_str
        assert "test_component" in repr_str
        assert "state=stopped" in repr_str
        assert "health=unknown" in repr_str


class TestProviderComponent:
    """Test ProviderComponent functionality."""

    def test_provider_component_creation(self):
        """Test creating a provider component."""
        provider = MockProvider("test_provider")
        registry = ProviderRegistry()

        component = ProviderComponent("test_component", provider, registry)

        assert component.name == "test_component"
        assert component.provider == provider
        assert component.registry == registry
        assert component.instance is None

    @pytest.mark.asyncio
    async def test_provider_component_start(self):
        """Test starting a provider component."""
        provider = MockProvider("test_provider")
        registry = ProviderRegistry()
        component = ProviderComponent("test_component", provider, registry)

        # Start component
        await component.start()

        assert component.state == LifecycleState.STARTED
        assert component.health_status == HealthStatus.HEALTHY
        assert component.instance is not None
        assert provider.create_called
        assert component.get_startup_time() is not None

    @pytest.mark.asyncio
    async def test_provider_component_start_with_lifecycle(self):
        """Test starting a provider component with lifecycle methods."""

        def create_service(registry):
            return MockService("test_service", has_lifecycle=True)

        provider = MockProvider("test_provider", create_service)
        registry = ProviderRegistry()
        component = ProviderComponent("test_component", provider, registry)

        # Start component
        await component.start()

        assert component.state == LifecycleState.STARTED
        assert component.instance.started

    @pytest.mark.asyncio
    async def test_provider_component_stop(self):
        """Test stopping a provider component."""
        provider = MockProvider("test_provider")
        registry = ProviderRegistry()
        component = ProviderComponent("test_component", provider, registry)

        # Start then stop
        await component.start()
        await component.stop()

        assert component.state == LifecycleState.STOPPED
        assert component.health_status == HealthStatus.UNKNOWN
        assert component.instance is None
        assert component.get_shutdown_time() is not None

    @pytest.mark.asyncio
    async def test_provider_component_stop_with_lifecycle(self):
        """Test stopping a provider component with lifecycle methods."""

        def create_service(registry):
            return MockService("test_service", has_lifecycle=True)

        provider = MockProvider("test_provider", create_service)
        registry = ProviderRegistry()
        component = ProviderComponent("test_component", provider, registry)

        # Start then stop
        await component.start()
        service = component.instance
        await component.stop()

        assert service.stopped

    @pytest.mark.asyncio
    async def test_provider_component_health_check(self):
        """Test provider component health check."""

        def create_service(registry):
            return MockService("test_service", has_health_check=True)

        provider = MockProvider("test_provider", create_service)
        registry = ProviderRegistry()
        component = ProviderComponent("test_component", provider, registry)

        # Start component
        await component.start()

        # Health check
        status = await component.health_check()
        assert status == HealthStatus.HEALTHY
        assert component.get_last_health_check_time() is not None

    @pytest.mark.asyncio
    async def test_provider_component_start_failure(self):
        """Test provider component start failure."""

        def failing_create(registry):
            raise RuntimeError("Provider creation failed")

        provider = MockProvider("test_provider", failing_create)
        registry = ProviderRegistry()
        component = ProviderComponent("test_component", provider, registry)

        # Start should fail
        with pytest.raises(RuntimeError, match="Failed to start component"):
            await component.start()

        assert component.state == LifecycleState.FAILED
        assert component.health_status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_provider_component_invalid_state(self):
        """Test provider component with invalid state transitions."""
        provider = MockProvider("test_provider")
        registry = ProviderRegistry()
        component = ProviderComponent("test_component", provider, registry)

        # Start component
        await component.start()

        # Try to start again
        with pytest.raises(RuntimeError, match="Component .* is not in stopped state"):
            await component.start()


class TestLifecycleManager:
    """Test LifecycleManager functionality."""

    def test_manager_creation(self):
        """Test creating a lifecycle manager."""
        manager = LifecycleManager()

        assert manager.startup_timeout == 30.0
        assert manager.shutdown_timeout == 30.0
        assert manager.components == {}
        assert manager.get_health_check_interval() == 30.0

    def test_manager_custom_timeouts(self):
        """Test creating manager with custom timeouts."""
        manager = LifecycleManager(startup_timeout=60.0, shutdown_timeout=45.0)

        assert manager.startup_timeout == 60.0
        assert manager.shutdown_timeout == 45.0

    def test_register_component(self):
        """Test registering components."""
        manager = LifecycleManager()
        component = MockComponent("test_component")

        manager.register_component(component)

        assert "test_component" in manager.components
        assert manager.components["test_component"] == component

    def test_register_duplicate_component(self):
        """Test registering duplicate component."""
        manager = LifecycleManager()
        component1 = MockComponent("test_component")
        component2 = MockComponent("test_component")

        manager.register_component(component1)

        with pytest.raises(
            ValueError, match="Component 'test_component' is already registered"
        ):
            manager.register_component(component2)

    def test_register_invalid_component(self):
        """Test registering invalid component."""
        manager = LifecycleManager()

        with pytest.raises(
            ValueError, match="Component must be a LifecycleComponent"
        ):
            manager.register_component("not a component")

    def test_unregister_component(self):
        """Test unregistering components."""
        manager = LifecycleManager()
        component = MockComponent("test_component")

        manager.register_component(component)
        manager.unregister_component("test_component")

        assert "test_component" not in manager.components

    def test_unregister_nonexistent_component(self):
        """Test unregistering non-existent component."""
        manager = LifecycleManager()

        with pytest.raises(
            ValueError, match="Component 'nonexistent' is not registered"
        ):
            manager.unregister_component("nonexistent")

    def test_add_dependency(self):
        """Test adding dependencies between components."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1")
        comp2 = MockComponent("component2")

        manager.register_component(comp1)
        manager.register_component(comp2)

        # component2 depends on component1
        manager.add_dependency("component2", "component1")

        assert "component1" in comp2.dependencies
        assert "component2" in comp1.dependents

    def test_add_circular_dependency(self):
        """Test detecting circular dependencies."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1")
        comp2 = MockComponent("component2")
        comp3 = MockComponent("component3")

        manager.register_component(comp1)
        manager.register_component(comp2)
        manager.register_component(comp3)

        # Create dependency chain: comp3 -> comp2 -> comp1
        manager.add_dependency("component2", "component1")
        manager.add_dependency("component3", "component2")

        # Try to create circular dependency: comp1 -> comp3
        with pytest.raises(
            LifecycleDependencyError, match="circular dependency"
        ):
            manager.add_dependency("component1", "component3")

    def test_get_startup_order(self):
        """Test getting startup order."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1")  # No dependencies
        comp2 = MockComponent("component2")  # Depends on comp1
        comp3 = MockComponent("component3")  # Depends on comp2

        manager.register_component(comp1)
        manager.register_component(comp2)
        manager.register_component(comp3)

        manager.add_dependency("component2", "component1")
        manager.add_dependency("component3", "component2")

        startup_order = manager.get_startup_order()

        # component1 should start first, then component2, then component3
        assert startup_order.index("component1") < startup_order.index("component2")
        assert startup_order.index("component2") < startup_order.index("component3")

    def test_get_shutdown_order(self):
        """Test getting shutdown order."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1")
        comp2 = MockComponent("component2")
        comp3 = MockComponent("component3")

        manager.register_component(comp1)
        manager.register_component(comp2)
        manager.register_component(comp3)

        manager.add_dependency("component2", "component1")
        manager.add_dependency("component3", "component2")

        shutdown_order = manager.get_shutdown_order()

        # component3 should stop first, then component2, then component1
        assert shutdown_order.index("component3") < shutdown_order.index("component2")
        assert shutdown_order.index("component2") < shutdown_order.index("component1")

    @pytest.mark.asyncio
    async def test_start_all_components(self):
        """Test starting all components."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1")
        comp2 = MockComponent("component2")

        manager.register_component(comp1)
        manager.register_component(comp2)
        manager.add_dependency("component2", "component1")

        await manager.start_all()

        assert comp1.start_called
        assert comp2.start_called
        assert comp1.state == LifecycleState.STARTED
        assert comp2.state == LifecycleState.STARTED

        # Cleanup
        await manager.stop_all()

    @pytest.mark.asyncio
    async def test_stop_all_components(self):
        """Test stopping all components."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1")
        comp2 = MockComponent("component2")

        manager.register_component(comp1)
        manager.register_component(comp2)
        manager.add_dependency("component2", "component1")

        await manager.start_all()
        await manager.stop_all()

        assert comp1.stop_called
        assert comp2.stop_called
        assert comp1.state == LifecycleState.STOPPED
        assert comp2.state == LifecycleState.STOPPED

    @pytest.mark.asyncio
    async def test_start_component_failure(self):
        """Test handling component start failure."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1", start_should_fail=True)

        manager.register_component(comp1)

        with pytest.raises(
            LifecycleError, match="Component component1 failed to start"
        ):
            await manager.start_all()

    @pytest.mark.asyncio
    async def test_start_component_timeout(self):
        """Test handling component start timeout."""
        manager = LifecycleManager(startup_timeout=0.1)
        comp1 = MockComponent("component1", start_delay=0.2)

        manager.register_component(comp1)

        with pytest.raises(LifecycleTimeoutError, match="startup timed out"):
            await manager.start_all()

    @pytest.mark.asyncio
    async def test_stop_component_failure(self):
        """Test handling component stop failure."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1", stop_should_fail=True)

        manager.register_component(comp1)

        await manager.start_all()

        with pytest.raises(
            LifecycleError, match="Some components failed to stop"
        ):
            await manager.stop_all()

    @pytest.mark.asyncio
    async def test_start_specific_component(self):
        """Test starting a specific component."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1")
        comp2 = MockComponent("component2")
        comp3 = MockComponent("component3")

        manager.register_component(comp1)
        manager.register_component(comp2)
        manager.register_component(comp3)

        manager.add_dependency("component2", "component1")
        manager.add_dependency("component3", "component2")

        # Start component2 - should start component1 and component2 but not component3
        await manager.start_component("component2")

        assert comp1.start_called
        assert comp2.start_called
        assert not comp3.start_called

        # Cleanup
        await manager.stop_all()

    @pytest.mark.asyncio
    async def test_stop_specific_component(self):
        """Test stopping a specific component."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1")
        comp2 = MockComponent("component2")
        comp3 = MockComponent("component3")

        manager.register_component(comp1)
        manager.register_component(comp2)
        manager.register_component(comp3)

        manager.add_dependency("component2", "component1")
        manager.add_dependency("component3", "component2")

        await manager.start_all()

        # Stop component2 - should stop component3 and component2 but not component1
        await manager.stop_component("component2")

        assert not comp1.stop_called
        assert comp2.stop_called
        assert comp3.stop_called

        # Cleanup
        await manager.stop_all()

    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """Test health checking all components."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1")
        comp2 = MockComponent("component2")

        manager.register_component(comp1)
        manager.register_component(comp2)

        results = await manager.health_check_all()

        assert len(results) == 2
        assert results["component1"] == HealthStatus.UNKNOWN
        assert results["component2"] == HealthStatus.UNKNOWN
        assert comp1.health_check_called
        assert comp2.health_check_called

    def test_get_component_status(self):
        """Test getting component status information."""
        manager = LifecycleManager()
        comp1 = MockComponent("component1")
        comp2 = MockComponent("component2")

        manager.register_component(comp1)
        manager.register_component(comp2)
        manager.add_dependency("component2", "component1")

        status = manager.get_component_status()

        assert len(status) == 2
        assert status["component1"]["state"] == "stopped"
        assert status["component1"]["health_status"] == "unknown"
        assert status["component1"]["dependencies"] == []
        assert status["component1"]["dependents"] == ["component2"]

        assert status["component2"]["state"] == "stopped"
        assert status["component2"]["dependencies"] == ["component1"]
        assert status["component2"]["dependents"] == []

    def test_set_health_check_interval(self):
        """Test setting health check interval."""
        manager = LifecycleManager()

        manager.set_health_check_interval(60.0)
        assert manager.get_health_check_interval() == 60.0

        # Invalid interval
        with pytest.raises(ValueError, match="Health check interval must be positive"):
            manager.set_health_check_interval(0)

    @pytest.mark.asyncio
    async def test_health_monitoring(self):
        """Test health check monitoring."""
        manager = LifecycleManager()
        manager.set_health_check_interval(0.1)  # Fast interval for testing

        comp1 = MockComponent("component1")
        manager.register_component(comp1)

        # Start components and health monitoring
        await manager.start_all()

        # Wait a bit for health checks
        await asyncio.sleep(0.2)

        # Health checks should have been called
        assert comp1.health_check_called

        # Stop components and health monitoring
        await manager.stop_all()


class TestLifecycleIntegration:
    """Integration tests for lifecycle management."""

    @pytest.mark.asyncio
    async def test_complex_dependency_graph(self):
        """Test complex dependency graph management."""
        manager = LifecycleManager()

        # Create components: A -> B, A -> C, B -> D, C -> D
        comp_a = MockComponent("A")
        comp_b = MockComponent("B")
        comp_c = MockComponent("C")
        comp_d = MockComponent("D")

        manager.register_component(comp_a)
        manager.register_component(comp_b)
        manager.register_component(comp_c)
        manager.register_component(comp_d)

        manager.add_dependency("B", "A")
        manager.add_dependency("C", "A")
        manager.add_dependency("D", "B")
        manager.add_dependency("D", "C")

        # Get startup order - D should be last, A should be first
        startup_order = manager.get_startup_order()

        assert startup_order.index("A") == 0  # A has no dependencies
        assert startup_order.index("D") == 3  # D depends on everything
        assert startup_order.index("B") > startup_order.index("A")
        assert startup_order.index("C") > startup_order.index("A")

        # Test startup and shutdown
        await manager.start_all()

        assert all(comp.start_called for comp in [comp_a, comp_b, comp_c, comp_d])

        await manager.stop_all()

        assert all(comp.stop_called for comp in [comp_a, comp_b, comp_c, comp_d])

    @pytest.mark.asyncio
    async def test_provider_component_integration(self):
        """Test integration with provider components."""

        # Create provider and service
        def create_service(registry):
            return MockService(
                "test_service", has_lifecycle=True, has_health_check=True
            )

        provider = MockProvider("test_provider", create_service)
        registry = ProviderRegistry()

        # Create lifecycle manager and provider component
        manager = LifecycleManager()
        component = ProviderComponent("test_component", provider, registry)

        manager.register_component(component)

        # Test full lifecycle
        await manager.start_all()

        assert component.state == LifecycleState.STARTED
        assert component.instance.started

        # Test health check
        health_results = await manager.health_check_all()
        assert health_results["test_component"] == HealthStatus.HEALTHY

        await manager.stop_all()

        assert component.state == LifecycleState.STOPPED
        assert component.instance is None

    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self):
        """Test handling partial startup failures."""
        manager = LifecycleManager()

        comp1 = MockComponent("component1")
        comp2 = MockComponent("component2", start_should_fail=True)
        comp3 = MockComponent("component3")

        manager.register_component(comp1)
        manager.register_component(comp2)
        manager.register_component(comp3)

        manager.add_dependency("component3", "component2")

        # Start should fail due to component2 failure
        with pytest.raises(LifecycleError):
            await manager.start_all()

        # component1 should have started, component2 failed, component3 not started
        assert comp1.start_called
        assert comp2.start_called
        assert not comp3.start_called

        # Should be able to stop what was started
        await manager.stop_all()
        assert comp1.stop_called
