"""Joyride Dependency Injection Container - Provider Pattern Implementation.

This package provides a comprehensive dependency injection system with multiple
provider types and automatic dependency resolution.
"""

from .class_provider import ClassProvider
from .factory_provider import FactoryProvider
from .prototype_provider import PrototypeProvider
from .provider_base import (
    CircularDependencyError,
    Dependency,
    DependencyResolutionError,
    LifecycleType,
    ProviderBase,
    ProviderInfo,
)
from .provider_registry import ProviderRegistry
from .singleton_provider import SingletonProvider

__all__ = [
    # Base types and exceptions
    "LifecycleType",
    "CircularDependencyError",
    "DependencyResolutionError",
    "Dependency",
    "ProviderInfo",
    "ProviderBase",
    # Provider implementations
    "SingletonProvider",
    "FactoryProvider",
    "PrototypeProvider",
    "ClassProvider",
    # Registry
    "ProviderRegistry",
]
