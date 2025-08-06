"""Test provider adapter integration."""

import asyncio

import pytest

from app.joyride.injection.lifecycle.component import ComponentState
from app.joyride.injection.lifecycle.provider_adapter import ProviderComponent
from app.joyride.injection.providers.provider_base import Dependency, ProviderBase
from app.joyride.injection.providers.provider_registry import ProviderRegistry


class MockInstance:
    """Mock instance created by provider."""

    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.started = False
        self.stopped = False
        self.start_called = False
        self.stop_called = False
        self.health_status = True

    async def start(self) -> None:
        """Mock async start method."""
        if self.should_fail:
            raise RuntimeError(f"Failed to start {self.name}")
        self.started = True
        self.start_called = True

    async def stop(self) -> None:
        """Mock async stop method."""
        if self.should_fail:
            raise RuntimeError(f"Failed to stop {self.name}")
        self.stopped = True
        self.stop_called = True

    def health_check(self) -> bool:
        """Mock health check method."""
        return self.health_status and self.started

    def set_health(self, status: bool) -> None:
        """Set health status for testing."""
        self.health_status = status


class SyncMockInstance:
    """Mock instance with synchronous methods."""

    def __init__(self, name: str):
        self.name = name
        self.started = False
        self.stopped = False

    def start(self) -> None:
        """Mock sync start method."""
        self.started = True

    def stop(self) -> None:
        """Mock sync stop method."""
        self.stopped = True

    def health_check(self) -> bool:
        """Mock sync health check."""
        return self.started


class MockProvider(ProviderBase):
    """Mock provider for testing."""

    def __init__(self, name: str, instance_type: str = "async"):
        super().__init__(name)
        self.instance_type = instance_type
        self.create_called = False
        self.cleanup_called = False
        self.should_fail = False

    def create(self, container: ProviderRegistry, **kwargs):
        """Create mock instance."""
        self.create_called = True
        if self.instance_type == "sync":
            return SyncMockInstance(self.name)
        else:
            return MockInstance(self.name, self.should_fail)

    def can_create(self, container: ProviderRegistry) -> bool:
        """Mock can_create."""
        return True

    def get_dependencies(self) -> list[Dependency]:
        """Mock dependencies."""
        return []

    def cleanup(self, instance) -> None:
        """Mock cleanup."""
        self.cleanup_called = True


@pytest.mark.asyncio
async def test_provider_component_basic_lifecycle():
    """Test basic provider component lifecycle."""
    provider = MockProvider("test_provider")
    registry = ProviderRegistry()

    component = ProviderComponent("test", provider, registry)

    assert component.instance is None
    assert component.state == ComponentState.CREATED

    # Start component
    await component.start()

    assert component.instance is not None
    assert isinstance(component.instance, MockInstance)
    assert component.instance.started is True
    assert component.state == ComponentState.STARTED
    assert provider.create_called is True

    # Stop component
    await component.stop()

    assert component.instance is None
    assert component.state == ComponentState.STOPPED
    assert provider.cleanup_called is True


@pytest.mark.asyncio
async def test_provider_component_health_check():
    """Test provider component health checking."""
    provider = MockProvider("test_provider")
    registry = ProviderRegistry()

    component = ProviderComponent("test", provider, registry)

    # Health check when not started (no instance)
    health = await component.health_check()
    assert health is False

    # Start and check health
    await component.start()
    health = await component.health_check()
    assert health is True

    # Change health status
    component.instance.set_health(False)
    health = await component.health_check()
    assert health is False

    # Stop and check
    await component.stop()
    health = await component.health_check()
    assert health is False


@pytest.mark.asyncio
async def test_provider_component_sync_methods():
    """Test provider component with sync start/stop methods."""
    provider = MockProvider("sync_provider", "sync")
    registry = ProviderRegistry()

    component = ProviderComponent("test", provider, registry)

    # Start component
    await component.start()

    assert component.instance is not None
    assert isinstance(component.instance, SyncMockInstance)
    assert component.instance.started is True
    assert component.state == ComponentState.STARTED

    # Stop component
    await component.stop()

    assert component.instance is None
    assert component.state == ComponentState.STOPPED


@pytest.mark.asyncio
async def test_provider_component_no_start_stop_methods():
    """Test provider component where instance has no start/stop methods."""

    class SimpleInstance:
        """Instance without start/stop methods."""

        def __init__(self, name: str):
            self.name = name

    class SimpleProvider(ProviderBase):
        """Provider that creates simple instance."""

        def __init__(self, name: str):
            super().__init__(name)

        def create(self, container: ProviderRegistry, **kwargs):
            return SimpleInstance(self.name)

        def can_create(self, container: ProviderRegistry) -> bool:
            return True

        def get_dependencies(self) -> list[Dependency]:
            return []

    provider = SimpleProvider("simple_provider")
    registry = ProviderRegistry()

    component = ProviderComponent("test", provider, registry)

    # Should start successfully even without start method
    await component.start()

    assert component.instance is not None
    assert component.state == ComponentState.STARTED

    # Health check should return True (default for no health_check method)
    health = await component.health_check()
    assert health is True

    # Should stop successfully even without stop method
    await component.stop()

    assert component.instance is None
    assert component.state == ComponentState.STOPPED


@pytest.mark.asyncio
async def test_provider_component_health_check_exceptions():
    """Test provider component handles health check exceptions."""

    class FailingHealthInstance:
        """Instance with failing health check."""

        def health_check(self):
            raise RuntimeError("Health check failed")

    class FailingHealthProvider(ProviderBase):
        """Provider that creates failing health instance."""

        def __init__(self, name: str):
            super().__init__(name)

        def create(self, container: ProviderRegistry, **kwargs):
            return FailingHealthInstance()

        def can_create(self, container: ProviderRegistry) -> bool:
            return True

        def get_dependencies(self) -> list[Dependency]:
            return []

    provider = FailingHealthProvider("failing_provider")
    registry = ProviderRegistry()

    component = ProviderComponent("test", provider, registry)

    await component.start()

    # Health check should return False on exception
    health = await component.health_check()
    assert health is False


@pytest.mark.asyncio
async def test_provider_component_health_status_conversion():
    """Test provider component health status conversion."""

    class EnumHealthInstance:
        """Instance with enum-like health status."""

        def __init__(self):
            self.health_value = "HEALTHY"

        def health_check(self):
            return self.health_value

        def set_health(self, value):
            self.health_value = value

    class EnumHealthProvider(ProviderBase):
        """Provider that creates enum health instance."""

        def __init__(self, name: str):
            super().__init__(name)

        def create(self, container: ProviderRegistry, **kwargs):
            return EnumHealthInstance()

        def can_create(self, container: ProviderRegistry) -> bool:
            return True

        def get_dependencies(self) -> list[Dependency]:
            return []

    provider = EnumHealthProvider("enum_provider")
    registry = ProviderRegistry()

    component = ProviderComponent("test", provider, registry)

    await component.start()

    # Test string conversion
    health = await component.health_check()
    assert health is True  # "HEALTHY" converts to True

    # Test unhealthy status
    component.instance.set_health("UNHEALTHY")
    health = await component.health_check()
    assert health is False

    # Test unknown status
    component.instance.set_health("UNKNOWN")
    health = await component.health_check()
    assert health is False


@pytest.mark.asyncio
async def test_provider_component_async_health_check():
    """Test provider component with async health check."""

    class AsyncHealthInstance:
        """Instance with async health check."""

        def __init__(self):
            self.healthy = True

        async def health_check(self):
            await asyncio.sleep(0.01)  # Simulate async work
            return self.healthy

        def set_health(self, status: bool):
            self.healthy = status

    class AsyncHealthProvider(ProviderBase):
        """Provider that creates async health instance."""

        def __init__(self, name: str):
            super().__init__(name)

        def create(self, container: ProviderRegistry, **kwargs):
            return AsyncHealthInstance()

        def can_create(self, container: ProviderRegistry) -> bool:
            return True

        def get_dependencies(self) -> list[Dependency]:
            return []

    provider = AsyncHealthProvider("async_provider")
    registry = ProviderRegistry()

    component = ProviderComponent("test", provider, registry)

    await component.start()

    # Test async health check
    health = await component.health_check()
    assert health is True

    # Change health status
    component.instance.set_health(False)
    health = await component.health_check()
    assert health is False
