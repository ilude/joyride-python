"""Test lifecycle orchestrator."""

import pytest
from app.joyride.injection.lifecycle.orchestrator import LifecycleOrchestrator
from app.joyride.injection.lifecycle.registry import ComponentRegistry
from app.joyride.injection.lifecycle.component import StartableComponent
from app.joyride.injection.lifecycle.types import LifecycleError


class MockComponent(StartableComponent):
    """Mock component with tracking."""
    
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
    comp1 = MockComponent("test1")
    comp2 = MockComponent("test2")
    
    await registry.register(comp1)
    await registry.register(comp2)
    
    # Start all
    await orchestrator.start_all()
    
    assert comp1.is_started()
    assert comp2.is_started()
    assert comp1.start_count == 1
    assert comp2.start_count == 1
    
    # Stop all
    await orchestrator.stop_all()
    
    assert comp1.is_stopped()
    assert comp2.is_stopped()
    assert comp1.stop_count == 1
    assert comp2.stop_count == 1


@pytest.mark.asyncio
async def test_orchestrator_dependencies():
    """Test dependency ordering."""
    registry = ComponentRegistry()
    orchestrator = LifecycleOrchestrator(registry)
    
    # Create components with dependencies
    comp1 = MockComponent("database")  # No dependencies
    comp2 = MockComponent("api")       # Depends on comp1
    comp3 = MockComponent("web")      # Depends on comp2
    
    comp2.add_dependency("database")
    comp3.add_dependency("api")
    
    await registry.register(comp1)
    await registry.register(comp2)
    await registry.register(comp3)
    
    # Start all - should start in dependency order
    await orchestrator.start_all()
    
    assert comp1.is_started()
    assert comp2.is_started()
    assert comp3.is_started()
    
    # Stop all - should stop in reverse order
    await orchestrator.stop_all()
    
    assert comp1.is_stopped()
    assert comp2.is_stopped()
    assert comp3.is_stopped()


@pytest.mark.asyncio
async def test_orchestrator_circular_dependency():
    """Test circular dependency detection."""
    registry = ComponentRegistry()
    orchestrator = LifecycleOrchestrator(registry)
    
    # Create circular dependency
    comp1 = MockComponent("comp1")
    comp2 = MockComponent("comp2")
    
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
    database = MockComponent("database")
    api = MockComponent("api")
    
    api.add_dependency("database")
    
    await registry.register(database)
    await registry.register(api)
    
    # Start database only
    await orchestrator.start_component("database")
    
    assert database.is_started()
    assert api.is_created()  # Still in created state
    
    # Start api (should not start database again)
    await orchestrator.start_component("api")
    
    assert database.is_started()
    assert api.is_started()
    
    # Stop api only
    await orchestrator.stop_component("api")
    
    assert database.is_started()
    assert api.is_stopped()


@pytest.mark.asyncio
async def test_orchestrator_error_handling():
    """Test error handling during shutdown."""
    registry = ComponentRegistry()
    orchestrator = LifecycleOrchestrator(registry)
    
    class FailingComponent(StartableComponent):
        async def _do_stop(self) -> None:
            raise RuntimeError("Stop failed")
    
    failing_comp = FailingComponent("failing")
    good_comp = MockComponent("good")
    
    await registry.register(failing_comp)
    await registry.register(good_comp)
    
    # Start both
    await orchestrator.start_all()
    
    # Stop all - should handle failure gracefully
    with pytest.raises(LifecycleError, match="Some components failed to stop"):
        await orchestrator.stop_all()
    
    # Good component should still be stopped
    assert good_comp.is_stopped()


@pytest.mark.asyncio
async def test_orchestrator_nonexistent_component():
    """Test error when component not found."""
    registry = ComponentRegistry()
    orchestrator = LifecycleOrchestrator(registry)
    
    with pytest.raises(LifecycleError, match="not found in startup order"):
        await orchestrator.start_component("nonexistent")
    
    with pytest.raises(LifecycleError, match="not found in shutdown order"):
        await orchestrator.stop_component("nonexistent")


@pytest.mark.asyncio
async def test_orchestrator_startup_order():
    """Test that startup order respects dependencies."""
    registry = ComponentRegistry()
    orchestrator = LifecycleOrchestrator(registry)
    
    # Track start order
    start_order = []
    
    class TrackingComponent(StartableComponent):
        async def _do_start(self) -> None:
            start_order.append(self.name)
    
    # Create dependency chain: A -> B -> C
    comp_a = TrackingComponent("A")
    comp_b = TrackingComponent("B")
    comp_c = TrackingComponent("C")
    
    comp_b.add_dependency("A")
    comp_c.add_dependency("B")
    
    # Register in random order
    await registry.register(comp_c)
    await registry.register(comp_a)
    await registry.register(comp_b)
    
    await orchestrator.start_all()
    
    # Should start in dependency order: A, B, C
    assert start_order == ["A", "B", "C"]
