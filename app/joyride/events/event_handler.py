"""
Event handler base class for the Joyride DNS Service.

This module defines the EventHandler abstract class that all
event-handling components must inherit from.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event


class EventHandler(ABC):
    """
    Abstract base class for components that handle events in the Joyride DNS Service.

    Implements the Strategy pattern by providing pluggable event handling
    logic. Handlers can filter events and implement specific business logic
    for different event types.

    All event handlers must implement handle() and can_handle() methods
    to ensure consistent behavior and proper event routing.
    """

    def __init__(self, name: str):
        """
        Initialize the event handler.

        Args:
            name: Unique name for this handler instance
        """
        self._name = name
        self._enabled = True

    @property
    def name(self) -> str:
        """Name of this handler."""
        return self._name

    @property
    def enabled(self) -> bool:
        """Whether this handler is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable this handler."""
        self._enabled = True

    def disable(self) -> None:
        """Disable this handler."""
        self._enabled = False

    @abstractmethod
    def can_handle(self, event: "Event") -> bool:
        """
        Check if this handler can process the given event.

        Args:
            event: Event to check

        Returns:
            True if this handler can process the event
        """
        pass

    @abstractmethod
    async def handle(self, event: "Event") -> None:
        """
        Handle the given event.

        This method should implement the specific business logic for
        processing the event. Should not raise exceptions - use proper
        error handling and logging instead.

        Args:
            event: Event to handle
        """
        pass

    def __str__(self) -> str:
        """String representation of the handler."""
        status = "enabled" if self.enabled else "disabled"
        return f"{self.__class__.__name__}('{self.name}', {status})"
