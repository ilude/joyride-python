"""Test health monitoring."""

import asyncio

import pytest

from app.joyride.injection.lifecycle.component import (
    ComponentState, HealthCheckableComponent)
from app.joyride.injection.lifecycle.health import HealthMonitor
from app.joyride.injection.lifecycle.registry import ComponentRegistry
from app.joyride.injection.lifecycle.types import HealthStatus


class MockHealthComponent(HealthCheckableComponent):
    """Component for health testing."""

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
        if self.state == ComponentState.STARTED:
            return self._health
        # Return appropriate status based on state when not started
        if self.state == ComponentState.CREATED:
            return HealthStatus.UNKNOWN
        elif self.state == ComponentState.FAILED:
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.UNKNOWN

    def set_health(self, health: HealthStatus) -> None:
        self._health = health


@pytest.mark.asyncio
async def test_health_monitor_basic():
    """Test basic health monitoring."""
    registry = ComponentRegistry()
    monitor = HealthMonitor(registry, check_interval=0.1)

    # Add healthy component
    comp1 = MockHealthComponent("comp1", HealthStatus.HEALTHY)
    await registry.register(comp1)

    # Check health
    health_results = await monitor.check_all()
    assert health_results["comp1"] == HealthStatus.UNKNOWN  # Component not started yet

    # Start component
    await comp1.start()
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
    comp1 = MockHealthComponent("comp1", HealthStatus.UNHEALTHY)
    await registry.register(comp1)

    # Start component so health check returns the configured health
    await comp1.start()

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

    comp1 = MockHealthComponent("comp1", HealthStatus.HEALTHY)
    await registry.register(comp1)
    await comp1.start()

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


@pytest.mark.asyncio
async def test_health_monitor_no_health_check():
    """Test components without health check method."""
    from app.joyride.injection.lifecycle.component import Component

    registry = ComponentRegistry()
    monitor = HealthMonitor(registry)

    # Component without health check method
    comp1 = Component("comp1")
    await registry.register(comp1)

    # Should return UNKNOWN
    health_results = await monitor.check_all()
    assert health_results["comp1"] == HealthStatus.UNKNOWN

    individual_health = await monitor.check_component("comp1")
    assert individual_health == HealthStatus.UNKNOWN


@pytest.mark.asyncio
async def test_health_monitor_start_stop():
    """Test starting and stopping health monitoring."""
    registry = ComponentRegistry()
    monitor = HealthMonitor(registry, check_interval=0.01)

    # Start monitoring
    await monitor.start_monitoring()
    assert monitor._monitoring_task is not None
    assert not monitor._monitoring_task.done()

    # Starting again should not create new task
    old_task = monitor._monitoring_task
    await monitor.start_monitoring()
    assert monitor._monitoring_task is old_task

    # Stop monitoring
    await monitor.stop_monitoring()
    assert monitor._monitoring_task.done()


@pytest.mark.asyncio
async def test_health_monitor_mixed_components():
    """Test monitoring mix of healthy and unhealthy components."""
    registry = ComponentRegistry()
    monitor = HealthMonitor(registry)

    # Add components with different health statuses
    healthy_comp = MockHealthComponent("healthy", HealthStatus.HEALTHY)
    unhealthy_comp = MockHealthComponent("unhealthy", HealthStatus.UNHEALTHY)
    degraded_comp = MockHealthComponent("degraded", HealthStatus.DEGRADED)

    await registry.register(healthy_comp)
    await registry.register(unhealthy_comp)
    await registry.register(degraded_comp)

    # Start components
    await healthy_comp.start()
    await unhealthy_comp.start()
    await degraded_comp.start()

    # Check all health
    health_results = await monitor.check_all()
    assert health_results["healthy"] == HealthStatus.HEALTHY
    assert health_results["unhealthy"] == HealthStatus.UNHEALTHY
    assert health_results["degraded"] == HealthStatus.DEGRADED

    # Only unhealthy should be in unhealthy list
    unhealthy = await monitor.get_unhealthy_components()
    assert len(unhealthy) == 1
    assert "unhealthy" in unhealthy
