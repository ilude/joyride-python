"""Base classes and types for Joyride Dependency Injection Container."""

import threading
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, List, Type, TypeVar

T = TypeVar("T")


class JoyrideLifecycleType(Enum):
    """Lifecycle types for component management."""

    SINGLETON = "singleton"
    FACTORY = "factory"
    PROTOTYPE = "prototype"


class JoyrideCircularDependencyError(Exception):
    """Raised when circular dependencies are detected."""

    pass


class JoyrideDependencyResolutionError(Exception):
    """Raised when dependency resolution fails."""

    pass


@dataclass
class JoyrideDependency:
    """Dependency specification for component injection."""

    name: str
    type_hint: Type[Any]
    required: bool = True
    default_value: Any = None

    def __post_init__(self):
        """Validate dependency after initialization."""
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Dependency name must be a non-empty string")

        # Check if type_hint is a valid type or generic type
        if not (
            isinstance(self.type_hint, type)
            or hasattr(self.type_hint, "__origin__")
            or hasattr(self.type_hint, "__module__")  # Generic types like Optional[str]
        ):  # Other typing constructs
            raise ValueError(f"Type hint must be a type, got {type(self.type_hint)}")


@dataclass
class JoyrideProviderInfo:
    """Information about a registered provider."""

    name: str
    provider: "JoyrideProvider[Any]"
    lifecycle: JoyrideLifecycleType
    dependencies: List[JoyrideDependency] = field(default_factory=list)
    created_instances: List[weakref.ReferenceType] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate provider info after initialization."""
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Provider name must be a non-empty string")
        if not isinstance(self.provider, JoyrideProvider):
            raise ValueError("Provider must be a JoyrideProvider instance")
        if not isinstance(self.lifecycle, JoyrideLifecycleType):
            raise ValueError("Lifecycle must be a JoyrideLifecycleType")


class JoyrideProvider(ABC, Generic[T]):
    """Abstract base class for all component providers."""

    def __init__(self, name: str):
        """Initialize provider with name."""
        if not isinstance(name, str) or not name:
            raise ValueError("Provider name must be a non-empty string")
        self.name = name
        self._lock = threading.RLock()

    @abstractmethod
    def create(self, container: "JoyrideProviderRegistry", **kwargs) -> T:
        """Create and return an instance of the managed component."""
        pass

    @abstractmethod
    def can_create(self, container: "JoyrideProviderRegistry") -> bool:
        """Check if the provider can create instances in the current context."""
        pass

    @abstractmethod
    def get_dependencies(self) -> List[JoyrideDependency]:
        """Get the dependencies required by this provider."""
        pass

    def cleanup(self, instance: T) -> None:
        """Clean up an instance when it's no longer needed."""
        pass
