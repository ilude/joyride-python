"""Prototype Provider Implementation for Joyride Dependency Injection Container."""

from typing import List

from .base import JoyrideDependency, JoyrideProvider, T


class JoyridePrototypeProvider(JoyrideProvider[T]):
    """Provider that creates instances from a prototype (clone pattern)."""

    def __init__(self, name: str, prototype: T, clone_method: str = "copy"):
        """Initialize prototype provider."""
        super().__init__(name)

        if not hasattr(prototype, clone_method):
            raise ValueError(f"Prototype does not have method '{clone_method}'")

        self._prototype = prototype
        self._clone_method = clone_method

    def create(self, container: "JoyrideProviderRegistry", **kwargs) -> T:
        """Create instance by cloning the prototype."""
        clone_func = getattr(self._prototype, self._clone_method)
        return clone_func()

    def can_create(self, container: "JoyrideProviderRegistry") -> bool:
        """Check if prototype can create instances."""
        return True

    def get_dependencies(self) -> List[JoyrideDependency]:
        """Get dependencies for this provider."""
        return []
