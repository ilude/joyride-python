"""Integration tests for complete lifecycle system."""

import pytest

from app.joyride.injection.lifecycle import (ComponentState,
                                             HealthCheckableComponent,
                                             HealthStatus, StartableComponent,
                                             create_lifecycle_system)
from app.joyride.injection.lifecycle.component import ComponentStartupError


class IntegrationTestComponent(HealthCheckableComponent):
    """Component for integration testing."""

    def __init__(self, name: str, healthy: bool = True):
        super().__init__(name)
        self._healthy = healthy
        self.start_count = 0
        self.stop_count = 0

    async def _do_start(self) -> None:
        self.start_count += 1

    async def _do_stop(self) -> None:
        self.stop_count += 1

    async def _do_health_check(self) -> bool:
        return self._healthy

    def set_health(self, healthy: bool) -> None:
        self._healthy = healthy


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
    assert comp1.state == ComponentState.STARTED
    assert comp2.state == ComponentState.STARTED
    assert comp3.state == ComponentState.STARTED

    # Check health
    health_results = await health_monitor.check_all()
    assert health_results["database"] == HealthStatus.HEALTHY
    assert health_results["api"] == HealthStatus.HEALTHY
    assert health_results["web"] == HealthStatus.HEALTHY

    # Simulate health issue
    comp2.set_health(False)

    unhealthy = await health_monitor.get_unhealthy_components()
    assert "api" in unhealthy

    # Stop all
    await orchestrator.stop_all()

    # Stop monitoring
    await health_monitor.stop_monitoring()

    # Verify all stopped
    assert comp1.state == ComponentState.STOPPED
    assert comp2.state == ComponentState.STOPPED
    assert comp3.state == ComponentState.STOPPED


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

    assert database.state == ComponentState.STARTED
    assert api.state == ComponentState.CREATED

    # Start api (should not start database again)
    await orchestrator.start_component("api")

    assert database.state == ComponentState.STARTED
    assert api.state == ComponentState.STARTED

    # Stop api only
    await orchestrator.stop_component("api")

    assert database.state == ComponentState.STARTED
    assert api.state == ComponentState.STOPPED


@pytest.mark.asyncio
async def test_system_resilience():
    """Test system handles failures gracefully."""
    registry, orchestrator, health_monitor = create_lifecycle_system()

    # Component that fails to start
    class FailingComponent(StartableComponent):
        async def _do_start(self) -> None:
            raise RuntimeError("Startup failed")

    good_comp = IntegrationTestComponent("good")
    failing_comp = FailingComponent("failing")

    await registry.register(good_comp)
    await registry.register(failing_comp)

    # Start good component first (should work)
    await orchestrator.start_component("good")
    assert good_comp.state == ComponentState.STARTED

    # Try to start failing component (should fail)
    with pytest.raises(ComponentStartupError, match="Failed to start failing"):
        await orchestrator.start_component("failing")

    # Failing component should be in failed state
    assert failing_comp.state == ComponentState.FAILED

    # Good component should still be started
    assert good_comp.state == ComponentState.STARTED

    # Can still stop good component
    await orchestrator.stop_component("good")
    assert good_comp.state == ComponentState.STOPPED


@pytest.mark.asyncio
async def test_create_lifecycle_system_helper():
    """Test the helper function creates all components correctly."""
    registry, orchestrator, health_monitor = create_lifecycle_system()

    # Verify types
    from app.joyride.injection.lifecycle.health import HealthMonitor
    from app.joyride.injection.lifecycle.orchestrator import \
        LifecycleOrchestrator
    from app.joyride.injection.lifecycle.registry import ComponentRegistry

    assert isinstance(registry, ComponentRegistry)
    assert isinstance(orchestrator, LifecycleOrchestrator)
    assert isinstance(health_monitor, HealthMonitor)

    # Verify they're connected
    assert orchestrator._registry is registry
    assert health_monitor._registry is registry
