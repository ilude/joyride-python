"""Singleton Provider Implementation for Joyride Dependency Injection Container."""

from typing import Callable, List, Optional

from .base import JoyrideProvider, JoyrideDependency, JoyrideDependencyResolutionError, T


class JoyrideSingletonProvider(JoyrideProvider[T]):
    """Provider that creates and maintains a single instance (singleton pattern)."""
    
    def __init__(self, name: str, factory: Callable[..., T], dependencies: Optional[List[JoyrideDependency]] = None):
        """Initialize singleton provider."""
        super().__init__(name)
        if not callable(factory):
            raise ValueError("Factory must be callable")
        
        self._factory = factory
        self._dependencies = dependencies or []
        self._instance: Optional[T] = None
        self._created = False
    
    def create(self, container: 'JoyrideProviderRegistry', **kwargs) -> T:
        """Create or return the singleton instance."""
        with self._lock:
            if self._created and self._instance is not None:
                return self._instance
            
            # Resolve dependencies
            resolved_deps = {}
            for dep in self._dependencies:
                if dep.name in kwargs:
                    resolved_deps[dep.name] = kwargs[dep.name]
                elif dep.required:
                    try:
                        resolved_deps[dep.name] = container.get(dep.name)
                    except JoyrideDependencyResolutionError:
                        raise JoyrideDependencyResolutionError(
                            f"Cannot resolve required dependency '{dep.name}' for singleton {self.name}"
                        )
                else:
                    try:
                        resolved_deps[dep.name] = container.get(dep.name)
                    except JoyrideDependencyResolutionError:
                        if dep.default_value is not None:
                            resolved_deps[dep.name] = dep.default_value
            
            # Create instance
            self._instance = self._factory(**resolved_deps)
            self._created = True
            
            return self._instance
    
    def can_create(self, container: 'JoyrideProviderRegistry') -> bool:
        """Check if singleton can be created."""
        if self._created:
            return True
        
        for dep in self._dependencies:
            if dep.required and not container.has_provider(dep.name):
                return False
        
        return True
    
    def get_dependencies(self) -> List[JoyrideDependency]:
        """Get dependencies for this provider."""
        return self._dependencies.copy()
    
    def reset(self) -> None:
        """Reset the singleton (mainly for testing)."""
        with self._lock:
            if self._instance is not None:
                self.cleanup(self._instance)
            self._instance = None
            self._created = False
