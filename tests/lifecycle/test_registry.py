"""Test component registry."""

import pytest

from app.joyride.injection.lifecycle.component import Component, StartableComponent
from app.joyride.injection.lifecycle.registry import ComponentRegistry
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
