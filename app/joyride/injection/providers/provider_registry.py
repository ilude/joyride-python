"""Provider Registry Implementation for Joyride Dependency Injection Container."""

import threading
import weakref
from typing import Any, Callable, Dict, List, Optional, Type

from .class_provider import ClassProvider
from .factory_provider import FactoryProvider
from .prototype_provider import PrototypeProvider
from .provider_base import (CircularDependencyError, Dependency,
                            DependencyResolutionError, LifecycleType,
                            ProviderBase, ProviderInfo)
from .singleton_provider import SingletonProvider


class ProviderRegistry:
    """Registry for managing component providers and dependency resolution."""

    def __init__(self):
        """Initialize provider registry."""
        self._providers: Dict[str, ProviderInfo] = {}
        self._resolution_stack: List[str] = []
        self._lock = threading.RLock()

    def register_provider(
        self, provider: ProviderBase[Any], lifecycle: LifecycleType
    ) -> None:
        """Register a provider with the registry."""
        with self._lock:
            if provider.name in self._providers:
                raise ValueError(f"Provider '{provider.name}' is already registered")

            info = ProviderInfo(
                name=provider.name,
                provider=provider,
                lifecycle=lifecycle,
                dependencies=provider.get_dependencies(),
            )

            self._providers[provider.name] = info

    def register_singleton(
        self,
        name: str,
        factory: Callable[..., Any],
        dependencies: Optional[List[Dependency]] = None,
    ) -> SingletonProvider:
        """Register a singleton provider."""
        provider = SingletonProvider(name, factory, dependencies)
        self.register_provider(provider, LifecycleType.SINGLETON)
        return provider

    def register_factory(
        self,
        name: str,
        factory: Callable[..., Any],
        dependencies: Optional[List[Dependency]] = None,
    ) -> FactoryProvider:
        """Register a factory provider."""
        provider = FactoryProvider(name, factory, dependencies)
        self.register_provider(provider, LifecycleType.FACTORY)
        return provider

    def register_prototype(
        self, name: str, prototype: Any, clone_method: str = "copy"
    ) -> PrototypeProvider:
        """Register a prototype provider."""
        provider = PrototypeProvider(name, prototype, clone_method)
        self.register_provider(provider, LifecycleType.PROTOTYPE)
        return provider

    def register_class(
        self,
        name: str,
        cls: Type[Any],
        lifecycle: LifecycleType = LifecycleType.FACTORY,
    ) -> ClassProvider:
        """Register a class provider."""
        provider = ClassProvider(name, cls, lifecycle)
        self.register_provider(provider, lifecycle)
        return provider

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider from the registry."""
        with self._lock:
            if name not in self._providers:
                raise ValueError(f"Provider '{name}' is not registered")

            info = self._providers[name]
            for instance_ref in info.created_instances:
                instance = instance_ref()
                if instance is not None:
                    info.provider.cleanup(instance)

            del self._providers[name]

    def has_provider(self, name: str) -> bool:
        """Check if a provider is registered."""
        return name in self._providers

    def get_provider_names(self) -> List[str]:
        """Get list of registered provider names."""
        return list(self._providers.keys())

    def get_provider_count(self) -> int:
        """Get number of registered providers."""
        return len(self._providers)

    def get(self, name: str, **kwargs) -> Any:
        """Get an instance from a provider."""
        with self._lock:
            if name not in self._providers:
                raise DependencyResolutionError(f"Provider '{name}' is not registered")

            # Check for circular dependencies
            if name in self._resolution_stack:
                cycle = self._resolution_stack[self._resolution_stack.index(name) :] + [
                    name
                ]
                raise CircularDependencyError(
                    f"Circular dependency detected: {' -> '.join(cycle)}"
                )

            self._resolution_stack.append(name)

            try:
                info = self._providers[name]
                instance = info.provider.create(self, **kwargs)

                # Track instance for lifecycle management
                if info.lifecycle in (
                    LifecycleType.FACTORY,
                    LifecycleType.PROTOTYPE,
                ):
                    info.created_instances.append(weakref.ref(instance))

                return instance

            finally:
                self._resolution_stack.pop()

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get dependency graph for all providers."""
        graph = {}

        for name, info in self._providers.items():
            dependencies = []
            for dep in info.dependencies:
                if self.has_provider(dep.name):
                    dependencies.append(dep.name)
            graph[name] = dependencies

        return graph

    def validate_dependencies(self) -> List[str]:
        """Validate all provider dependencies."""
        errors = []

        for name, info in self._providers.items():
            for dep in info.dependencies:
                if dep.required and not self.has_provider(dep.name):
                    errors.append(
                        f"Provider '{name}' has missing required dependency '{dep.name}'"
                    )

        return errors

    def clear(self) -> None:
        """Clear all providers from the registry."""
        with self._lock:
            for info in self._providers.values():
                for instance_ref in info.created_instances:
                    instance = instance_ref()
                    if instance is not None:
                        info.provider.cleanup(instance)

            self._providers.clear()
            self._resolution_stack.clear()
