"""Factory Provider Implementation for Joyride Dependency Injection Container."""

from typing import TYPE_CHECKING, Callable, List, Optional

from .base import (
    JoyrideDependency,
    JoyrideDependencyResolutionError,
    JoyrideProvider,
    T,
)

if TYPE_CHECKING:
    from .registry import JoyrideProviderRegistry


class JoyrideFactoryProvider(JoyrideProvider[T]):
    """Provider that creates new instances each time (factory pattern)."""

    def __init__(
        self,
        name: str,
        factory: Callable[..., T],
        dependencies: Optional[List[JoyrideDependency]] = None,
    ):
        """Initialize factory provider."""
        super().__init__(name)
        if not callable(factory):
            raise ValueError("Factory must be callable")

        self._factory = factory
        self._dependencies = dependencies or []

    def create(self, container: "JoyrideProviderRegistry", **kwargs) -> T:
        """Create instance using factory function."""
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
                        f"Cannot resolve required dependency '{dep.name}' for factory {self.name}"
                    )
            else:
                try:
                    resolved_deps[dep.name] = container.get(dep.name)
                except JoyrideDependencyResolutionError:
                    if dep.default_value is not None:
                        resolved_deps[dep.name] = dep.default_value

        # Create new instance
        return self._factory(**resolved_deps)

    def can_create(self, container: "JoyrideProviderRegistry") -> bool:
        """Check if factory can create instances."""
        for dep in self._dependencies:
            if dep.required and not container.has_provider(dep.name):
                return False

        return True

    def get_dependencies(self) -> List[JoyrideDependency]:
        """Get dependencies for this provider."""
        return self._dependencies.copy()
