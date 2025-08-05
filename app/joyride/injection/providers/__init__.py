"""Joyride Dependency Injection Container - Provider Pattern Implementation.

This package provides a comprehensive dependency injection system with multiple
provider types and automatic dependency resolution.
"""

from .base import (
    JoyrideCircularDependencyError,
    JoyrideDependency,
    JoyrideDependencyResolutionError,
    JoyrideLifecycleType,
    JoyrideProvider,
    JoyrideProviderInfo,
)
from .class_provider import JoyrideClassProvider
from .factory_provider import JoyrideFactoryProvider
from .prototype_provider import JoyridePrototypeProvider
from .registry import JoyrideProviderRegistry
from .singleton_provider import JoyrideSingletonProvider

__all__ = [
    # Base types and exceptions
    "JoyrideLifecycleType",
    "JoyrideCircularDependencyError",
    "JoyrideDependencyResolutionError",
    "JoyrideDependency",
    "JoyrideProviderInfo",
    "JoyrideProvider",
    # Provider implementations
    "JoyrideSingletonProvider",
    "JoyrideFactoryProvider",
    "JoyridePrototypeProvider",
    "JoyrideClassProvider",
    # Registry
    "JoyrideProviderRegistry",
]
