"""Component registry implementation."""

import asyncio
from typing import Dict, List, Optional

from .component import Component, ComponentState
from .interfaces import Logger
from .types import ComponentNotFoundError


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
            if component.state not in (ComponentState.STOPPED, ComponentState.FAILED):
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
