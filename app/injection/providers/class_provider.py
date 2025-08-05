"""Class Provider Implementation for Joyride Dependency Injection Container."""

import inspect
from typing import Any, List, Optional, Type, Union

from .base import (
    JoyrideDependency,
    JoyrideDependencyResolutionError,
    JoyrideLifecycleType,
    JoyrideProvider,
    T,
)


class JoyrideClassProvider(JoyrideProvider[T]):
    """Provider that creates instances from a class with automatic dependency injection."""

    def __init__(
        self,
        name: str,
        cls: Type[T],
        lifecycle: JoyrideLifecycleType = JoyrideLifecycleType.FACTORY,
    ):
        """Initialize class provider."""
        super().__init__(name)

        if not isinstance(cls, type):
            raise ValueError("cls must be a class")

        self._cls = cls
        self._lifecycle = lifecycle
        self._dependencies = self._analyze_dependencies()

        # For singleton lifecycle
        self._instance: Optional[T] = None
        self._created = False

    def _analyze_dependencies(self) -> List[JoyrideDependency]:
        """Analyze class constructor to determine dependencies."""
        dependencies = []

        try:
            sig = inspect.signature(self._cls.__init__)
        except (ValueError, TypeError):
            return dependencies

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            type_hint = (
                param.annotation if param.annotation != inspect.Parameter.empty else Any
            )

            # Handle Optional types (Union[Type, None])
            required = param.default == inspect.Parameter.empty
            if hasattr(type_hint, "__origin__") and hasattr(type_hint, "__args__"):
                origin = getattr(type_hint, "__origin__", None)
                args = getattr(type_hint, "__args__", ())

                if origin is Union and len(args) == 2 and type(None) in args:
                    required = False
                    type_hint = next(arg for arg in args if arg is not type(None))

            default_value = param.default if not required else None

            dependencies.append(
                JoyrideDependency(
                    name=param_name,
                    type_hint=type_hint,
                    required=required,
                    default_value=default_value,
                )
            )

        return dependencies

    def create(self, container: "JoyrideProviderRegistry", **kwargs) -> T:
        """Create instance using class constructor."""
        with self._lock:
            if self._lifecycle == JoyrideLifecycleType.SINGLETON and self._created:
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
                            f"Cannot resolve required dependency '{dep.name}' for class {self._cls.__name__}"
                        )
                else:
                    try:
                        resolved_deps[dep.name] = container.get(dep.name)
                    except JoyrideDependencyResolutionError:
                        if dep.default_value is not None:
                            resolved_deps[dep.name] = dep.default_value

            # Create instance
            instance = self._cls(**resolved_deps)

            if self._lifecycle == JoyrideLifecycleType.SINGLETON:
                self._instance = instance
                self._created = True

            return instance

    def can_create(self, container: "JoyrideProviderRegistry") -> bool:
        """Check if class can be instantiated."""
        if self._lifecycle == JoyrideLifecycleType.SINGLETON and self._created:
            return True

        for dep in self._dependencies:
            if dep.required and not container.has_provider(dep.name):
                return False

        return True

    def get_dependencies(self) -> List[JoyrideDependency]:
        """Get dependencies for this provider."""
        return self._dependencies.copy()
