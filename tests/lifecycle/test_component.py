"""
Tests for component lifecycle management.
"""
import asyncio
import time

import pytest

from app.joyride.injection.lifecycle.component import (
    Component,
    ComponentShutdownError,
    ComponentStartupError,
    ComponentState,
    ComponentStateError,
    HealthCheckableComponent,
    StartableComponent,
)


class TestComponent:
    """Test cases for base Component class."""

    def test_component_creation(self):
        """Test component creation with default state."""
        component = Component("test_component")
        assert component.name == "test_component"
        assert component.state == ComponentState.CREATED
        assert component.dependencies == set()
        assert component.get_dependents() == set()
        assert component.get_startup_time() is None
        assert component.get_shutdown_time() is None

    def test_dependency_management(self):
        """Test adding and retrieving dependencies."""
        component = Component("test_component")
        component.add_dependency("dep1")
        component.add_dependency("dep2")

        assert component.get_dependencies() == {"dep1", "dep2"}

        # Test that returned set is a copy
        deps = component.get_dependencies()
        deps.add("dep3")
        assert component.get_dependencies() == {"dep1", "dep2"}

    def test_dependent_management(self):
        """Test adding and retrieving dependents."""
        component = Component("test_component")
        component.add_dependent("dependent1")
        component.add_dependent("dependent2")

        assert component.get_dependents() == {"dependent1", "dependent2"}

    def test_metadata_management(self):
        """Test setting and getting metadata."""
        component = Component("test_component")
        component.set_metadata("key1", "value1")
        component.set_metadata("key2", 42)

        assert component.get_metadata("key1") == "value1"
        assert component.get_metadata("key2") == 42
        assert component.get_metadata("nonexistent") is None
        assert component.get_metadata("nonexistent", "default") == "default"

    def test_state_predicates(self):
        """Test state predicate methods."""
        component = Component("test_component")

        # Test CREATED state
        assert component.is_created()
        assert not component.is_starting()
        assert not component.is_started()
        assert not component.is_stopping()
        assert not component.is_stopped()
        assert not component.is_failed()

        # Test other states
        component.state = ComponentState.STARTING
        assert not component.is_created()
        assert component.is_starting()

        component.state = ComponentState.STARTED
        assert component.is_started()

        component.state = ComponentState.STOPPING
        assert component.is_stopping()

        component.state = ComponentState.STOPPED
        assert component.is_stopped()

        component.state = ComponentState.FAILED
        assert component.is_failed()

    def test_add_dependency_wrong_state(self):
        """Test that dependencies cannot be added after creation."""
        component = Component("test_component")
        component.state = ComponentState.STARTED

        with pytest.raises(ComponentStateError) as exc_info:
            component.add_dependency("dep1")

        assert "Cannot add dependencies" in str(exc_info.value)
        assert "started" in str(exc_info.value)

    def test_component_repr(self):
        """Test string representation of component."""
        component = Component("test_component")
        repr_str = repr(component)
        assert "Component" in repr_str
        assert "test_component" in repr_str
        assert "created" in repr_str


class TestStartableComponent:
    """Test cases for StartableComponent class."""

    @pytest.mark.asyncio
    async def test_start_success(self):
        """Test successful component start."""
        component = StartableComponent("test_component")

        await component.start()

        assert component.is_started()
        assert component.get_startup_time() is not None
        assert component.get_startup_time() >= 0

    @pytest.mark.asyncio
    async def test_stop_success(self):
        """Test successful component stop."""
        component = StartableComponent("test_component")
        await component.start()

        await component.stop()

        assert component.is_stopped()
        assert component.get_shutdown_time() is not None
        assert component.get_shutdown_time() >= 0

    @pytest.mark.asyncio
    async def test_start_wrong_state(self):
        """Test that start fails from wrong state."""
        component = StartableComponent("test_component")
        await component.start()

        # Try to start again while already started
        with pytest.raises(ComponentStateError) as exc_info:
            await component.start()

        assert "Cannot start" in str(exc_info.value)
        assert "started" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_stop_wrong_state(self):
        """Test that stop fails from wrong state."""
        component = StartableComponent("test_component")

        # Try to stop before starting
        with pytest.raises(ComponentStateError) as exc_info:
            await component.stop()

        assert "Cannot stop" in str(exc_info.value)
        assert "created" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_after_stop(self):
        """Test that component can be restarted after stopping."""
        component = StartableComponent("test_component")

        # Start, stop, start again
        await component.start()
        await component.stop()
        await component.start()

        assert component.is_started()

    @pytest.mark.asyncio
    async def test_custom_start_logic(self):
        """Test that custom start logic is called."""

        class TestComponent(StartableComponent):
            def __init__(self, name):
                super().__init__(name)
                self.start_called = False

            async def _do_start(self):
                self.start_called = True

        component = TestComponent("test_component")
        await component.start()

        assert component.start_called

    @pytest.mark.asyncio
    async def test_custom_stop_logic(self):
        """Test that custom stop logic is called."""

        class TestComponent(StartableComponent):
            def __init__(self, name):
                super().__init__(name)
                self.stop_called = False

            async def _do_stop(self):
                self.stop_called = True

        component = TestComponent("test_component")
        await component.start()
        await component.stop()

        assert component.stop_called

    @pytest.mark.asyncio
    async def test_start_failure(self):
        """Test component failure during start."""

        class FailingComponent(StartableComponent):
            async def _do_start(self):
                raise RuntimeError("Start failed")

        component = FailingComponent("failing_component")

        with pytest.raises(ComponentStartupError) as exc_info:
            await component.start()

        assert component.is_failed()
        assert "Failed to start" in str(exc_info.value)
        assert "Start failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_stop_failure(self):
        """Test component failure during stop."""

        class FailingComponent(StartableComponent):
            async def _do_stop(self):
                raise RuntimeError("Stop failed")

        component = FailingComponent("failing_component")
        await component.start()

        with pytest.raises(ComponentShutdownError) as exc_info:
            await component.stop()

        assert component.is_failed()
        assert "Failed to stop" in str(exc_info.value)
        assert "Stop failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_stop_from_failed_state(self):
        """Test that failed components can be stopped."""

        class FailingComponent(StartableComponent):
            async def _do_start(self):
                raise RuntimeError("Start failed")

        component = FailingComponent("failing_component")

        # Fail during start
        with pytest.raises(ComponentStartupError):
            await component.start()

        # Should be able to stop from failed state
        await component.stop()
        assert component.is_stopped()

    @pytest.mark.asyncio
    async def test_timing_metrics(self):
        """Test that timing metrics are recorded."""

        class SlowComponent(StartableComponent):
            async def _do_start(self):
                await asyncio.sleep(0.1)

            async def _do_stop(self):
                await asyncio.sleep(0.05)

        component = SlowComponent("slow_component")

        await component.start()
        assert component.get_startup_time() >= 0.1

        await component.stop()
        assert component.get_shutdown_time() >= 0.05


class TestHealthCheckableComponent:
    """Test cases for HealthCheckableComponent class."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        component = HealthCheckableComponent("test_component")
        await component.start()

        result = await component.health_check()

        assert result is True
        assert component.get_last_health_check() is not None

    @pytest.mark.asyncio
    async def test_health_check_not_started(self):
        """Test health check on non-started component."""
        component = HealthCheckableComponent("test_component")

        result = await component.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_custom_health_check(self):
        """Test custom health check logic."""

        class TestComponent(HealthCheckableComponent):
            def __init__(self, name):
                super().__init__(name)
                self.healthy = True

            async def _do_health_check(self):
                return self.healthy

        component = TestComponent("test_component")
        await component.start()

        # Should be healthy
        result = await component.health_check()
        assert result is True

        # Make unhealthy
        component.healthy = False
        result = await component.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        """Test health check timeout handling."""

        class SlowComponent(HealthCheckableComponent):
            async def _do_health_check(self):
                await asyncio.sleep(10)  # Longer than default timeout
                return True

        component = SlowComponent("slow_component")
        component.set_health_check_timeout(0.1)  # Short timeout
        await component.start()

        result = await component.health_check()
        assert result is False  # Should timeout

    @pytest.mark.asyncio
    async def test_health_check_exception(self):
        """Test health check exception handling."""

        class FailingComponent(HealthCheckableComponent):
            async def _do_health_check(self):
                raise RuntimeError("Health check failed")

        component = FailingComponent("failing_component")
        await component.start()

        result = await component.health_check()
        assert result is False

    def test_health_check_configuration(self):
        """Test health check configuration methods."""
        component = HealthCheckableComponent("test_component")

        # Test interval configuration
        component.set_health_check_interval(60.0)
        assert component.get_health_check_interval() == 60.0

        # Test timeout configuration
        component.set_health_check_timeout(10.0)
        assert component.get_health_check_timeout() == 10.0

    @pytest.mark.asyncio
    async def test_health_check_timestamp(self):
        """Test health check timestamp tracking."""
        component = HealthCheckableComponent("test_component")
        await component.start()

        assert component.get_last_health_check() is None

        before_check = time.time()
        await component.health_check()
        after_check = time.time()

        last_check = component.get_last_health_check()
        assert last_check is not None
        assert before_check <= last_check <= after_check


class TestComponentIntegration:
    """Integration tests for component interactions."""

    @pytest.mark.asyncio
    async def test_component_inheritance_chain(self):
        """Test that component inheritance works correctly."""

        # Create a component that uses all features
        class FullComponent(HealthCheckableComponent):
            def __init__(self, name):
                super().__init__(name)
                self.operations = []

            async def _do_start(self):
                self.operations.append("started")

            async def _do_stop(self):
                self.operations.append("stopped")

            async def _do_health_check(self):
                self.operations.append("health_checked")
                return len(self.operations) < 5  # Fail after 5 operations

        component = FullComponent("full_component")
        component.add_dependency("other_component")
        component.set_metadata("version", "1.0")

        # Test all functionality
        await component.start()
        assert component.is_started()
        assert "started" in component.operations

        result = await component.health_check()
        assert result is True
        assert "health_checked" in component.operations

        await component.stop()
        assert component.is_stopped()
        assert "stopped" in component.operations

        # Test that metadata and dependencies are preserved
        assert component.get_metadata("version") == "1.0"
        assert "other_component" in component.get_dependencies()

    def test_component_state_transitions(self):
        """Test valid component state transitions."""
        component = StartableComponent("test_component")

        # Test all valid state transitions
        valid_transitions = [
            (ComponentState.CREATED, ComponentState.STARTING),
            (ComponentState.STARTING, ComponentState.STARTED),
            (ComponentState.STARTING, ComponentState.FAILED),
            (ComponentState.STARTED, ComponentState.STOPPING),
            (ComponentState.STOPPING, ComponentState.STOPPED),
            (ComponentState.STOPPING, ComponentState.FAILED),
            (ComponentState.STOPPED, ComponentState.STARTING),
            (ComponentState.FAILED, ComponentState.STOPPING),
        ]

        for from_state, to_state in valid_transitions:
            component.state = from_state
            component.state = to_state  # Should not raise
            assert component.state == to_state


@pytest.fixture
def sample_component():
    """Fixture providing a sample component for testing."""
    return Component("sample_component")


@pytest.fixture
def sample_startable_component():
    """Fixture providing a sample startable component for testing."""
    return StartableComponent("sample_startable")


@pytest.fixture
def sample_health_component():
    """Fixture providing a sample health checkable component for testing."""
    return HealthCheckableComponent("sample_health")
