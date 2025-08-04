"""Test helper classes for injection system testing."""

import time
from typing import Optional


class SimpleServiceHelper:
    """Simple service for testing basic dependency injection."""
    __test__ = False

    def __init__(self, name: str = "test"):
        self.name = name
        self.initialized = True

    def copy(self):
        """Required for prototype providers."""
        return SimpleServiceHelper(self.name)


class DependentServiceHelper:
    """Service that depends on another service."""
    __test__ = False

    def __init__(self, service: SimpleServiceHelper, config: str = None):
        self.service = service
        self.config = config
        self.initialized = True


class ComplexServiceHelper:
    """Service with multiple dependencies."""
    __test__ = False

    def __init__(self, service: SimpleServiceHelper, dependent: DependentServiceHelper, config: Optional[str] = None):
        self.service = service
        self.dependent = dependent
        self.config = config


class PrototypeServiceHelper:
    """Service that can be cloned for prototype pattern."""
    __test__ = False

    def __init__(self, data=None):
        if isinstance(data, int):
            # Support integer values for compatibility with tests
            self.value = data
            self.data = data
        else:
            # Support dict values
            self.data = data or {}
            if hasattr(self, 'value'):
                pass  # Keep existing value if set
        self.created_at = time.time()

    def copy(self):
        """Custom copy method for prototype pattern."""
        if hasattr(self, 'value') and isinstance(self.value, int):
            # Handle integer data case
            return PrototypeServiceHelper(self.value)
        else:
            # Handle dict data case
            return PrototypeServiceHelper(self.data.copy() if hasattr(self.data, 'copy') else self.data)


# Aliases for public use
SimpleService = SimpleServiceHelper
DependentService = DependentServiceHelper
ComplexService = ComplexServiceHelper
PrototypeService = PrototypeServiceHelper
