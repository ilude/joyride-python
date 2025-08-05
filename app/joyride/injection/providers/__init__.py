"""Joyride Dependency Injection Container - Provider Pattern Implementation.

This package provides a comprehensive dependency injection system with multiple
provider types and automatic dependency resolution.
"""

from .base import (
    CircularDependencyError,
    Dependency,
    DependencyResolutionError,
    LifecycleType,
    Provider,
    ProviderInfo,
)
from .class_provider import ClassProvider
from .factory_provider import FactoryProvider
from .prototype_provider import PrototypeProvider
from .registry import ProviderRegistry
from .singleton_provider import SingletonProvider

__all__ = [
    # Base types and exceptions
    "LifecycleType",
    "CircularDependencyError",
    "DependencyResolutionError",
    "Dependency",
    "ProviderInfo",
    "Provider",
    # Provider implementations
    "SingletonProvider",
    "FactoryProvider",
    "PrototypeProvider",
    "ClassProvider",
    # Registry
    "ProviderRegistry",
]
