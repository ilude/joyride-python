"""Test helper classes for injection system testing."""

import time
from typing import Optional


class SimpleService:
    """Simple service for testing basic dependency injection."""

    def __init__(self, name: str = "test"):
        self.name = name
        self.initialized = True

    def copy(self):
        """Required for prototype providers."""
        return SimpleService(self.name)


class DependentService:
    """Service that depends on another service."""

    def __init__(self, service: "SimpleService", config: str = "default"):
        self.service = service
        self.config = config
        self.initialized = True


class ComplexService:
    """Service with multiple dependencies."""

    def __init__(
        self,
        service: "SimpleService",
        dependent: "DependentService",
        config: Optional[str] = None,
    ):
        self.service = service
        self.dependent = dependent
        self.config = config


class PrototypeService:
    """Service that can be cloned for prototype pattern."""

    def __init__(self, data=None):
        if isinstance(data, int):
            # Support integer values for compatibility with tests
            self.value = data
            self.data = data
        else:
            # Support dict values
            self.data = data or {}
            if hasattr(self, "value"):
                pass  # Keep existing value if set
        self.created_at = time.time()

    def copy(self):
        """Custom copy method for prototype pattern."""
        if hasattr(self, "value") and isinstance(self.value, int):
            # Handle integer data case
            return PrototypeService(self.value)
        else:
            # Handle dict data case
            return PrototypeService(
                self.data.copy() if hasattr(self.data, "copy") else self.data
            )
