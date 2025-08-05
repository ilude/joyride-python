"""
Joyride Dependency Injection Container

This module provides a comprehensive dependency injection system for the Joyride DNS Service,
implementing configuration management, component lifecycle, and service registration patterns.
"""

# Configuration system
from .config import JoyrideConfig, JoyrideConfigLoader, JoyrideConfigValidator

# Provider system
from .providers import (  # Base types and exceptions; Provider implementations; Registry
    JoyrideCircularDependencyError,
    JoyrideClassProvider,
    JoyrideDependency,
    JoyrideDependencyResolutionError,
    JoyrideFactoryProvider,
    JoyrideLifecycleType,
    JoyridePrototypeProvider,
    JoyrideProvider,
    JoyrideProviderInfo,
    JoyrideProviderRegistry,
    JoyrideSingletonProvider,
)

__all__ = [
    # Configuration
    "JoyrideConfig",
    "JoyrideConfigLoader",
    "JoyrideConfigValidator",
    # Provider system - Base types and exceptions
    "JoyrideLifecycleType",
    "JoyrideCircularDependencyError",
    "JoyrideDependencyResolutionError",
    "JoyrideDependency",
    "JoyrideProviderInfo",
    "JoyrideProvider",
    # Provider system - Implementations
    "JoyrideSingletonProvider",
    "JoyrideFactoryProvider",
    "JoyridePrototypeProvider",
    "JoyrideClassProvider",
    # Provider system - Registry
    "JoyrideProviderRegistry",
]
