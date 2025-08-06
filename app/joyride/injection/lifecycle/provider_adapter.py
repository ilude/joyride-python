"""Adapter for integrating providers with lifecycle system."""

import asyncio
from typing import Any, Optional

from ..providers.provider_base import ProviderBase
from ..providers.provider_registry import ProviderRegistry
from .component import HealthCheckableComponent


class ProviderComponent(HealthCheckableComponent):
    """Lifecycle component that wraps a provider."""

    def __init__(
        self, name: str, provider: ProviderBase, provider_registry: ProviderRegistry
    ):
        super().__init__(name)
        self._provider = provider
        self._provider_registry = provider_registry
        self.instance: Optional[Any] = None

    async def _do_start(self) -> None:
        """Start the provider."""
        # Create instance through provider
        self.instance = self._provider.create(self._provider_registry)

        # Call start method if it exists and instance is not None
        if self.instance is not None and hasattr(self.instance, "start"):
            if asyncio.iscoroutinefunction(self.instance.start):
                await self.instance.start()
            else:
                self.instance.start()

    async def _do_stop(self) -> None:
        """Stop the provider."""
        # Call stop method if it exists
        if self.instance is not None and hasattr(self.instance, "stop"):
            if asyncio.iscoroutinefunction(self.instance.stop):
                await self.instance.stop()
            else:
                self.instance.stop()

        # Clean up instance
        if self.instance is not None and hasattr(self._provider, "cleanup"):
            self._provider.cleanup(self.instance)

        self.instance = None

    async def _do_health_check(self) -> bool:
        """Check provider health."""
        # No instance means unhealthy
        if self.instance is None:
            return False

        # Check if instance has health_check method
        if hasattr(self.instance, "health_check"):
            try:
                result = self.instance.health_check()
                if asyncio.iscoroutine(result):
                    result = await result

                # Convert various types to bool
                return self._convert_to_bool(result)
            except Exception:
                return False

        # Default: healthy if started and has instance
        return True

    def _convert_to_bool(self, status: Any) -> bool:
        """Convert various health status types to bool."""
        if isinstance(status, bool):
            return status
        elif hasattr(status, "value"):  # Enum-like objects
            if hasattr(status, "name"):
                return status.name.upper() not in ("UNHEALTHY", "FAILED", "UNKNOWN")
            else:
                return str(status.value).upper() not in (
                    "unhealthy",
                    "failed",
                    "unknown",
                )
        elif isinstance(status, str):
            return status.lower() not in ("unhealthy", "failed", "unknown", "false")
        else:
            # Try to convert to bool directly
            try:
                return bool(status)
            except Exception:
                return False
