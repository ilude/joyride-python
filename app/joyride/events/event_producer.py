"""
Event producer base class for the Joyride DNS Service.

This module defines the EventProducer abstract class that all
event-producing components must inherit from.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .event import Event
    from .bus import EventBus


class EventProducer(ABC):
    """
    Abstract base class for components that produce events in the Joyride DNS Service.

    Implements the Observer pattern by allowing producers to publish events
    to the event bus. Provides lifecycle management and error handling
    capabilities for robust event production.

    All event producers must implement start(), stop(), and publish() methods
    to ensure consistent behavior across the system.
    """

    def __init__(self, name: str):
        """
        Initialize the event producer.

        Args:
            name: Unique name for this producer instance
        """
        self._name = name
        self._running = False
        self._event_bus: Optional["EventBus"] = None

    @property
    def name(self) -> str:
        """Name of this producer."""
        return self._name

    @property
    def is_running(self) -> bool:
        """Whether the producer is currently running."""
        return self._running

    @property
    def event_bus(self) -> Optional["EventBus"]:
        """Event bus this producer is connected to."""
        return self._event_bus

    def set_event_bus(self, event_bus: "EventBus") -> None:
        """
        Set the event bus for this producer.

        Args:
            event_bus: Event bus to connect to
        """
        self._event_bus = event_bus

    @abstractmethod
    async def start(self) -> None:
        """
        Start the event producer.

        This method should initialize any resources needed for event production
        and begin monitoring for events. Must be idempotent.

        Raises:
            RuntimeError: If producer fails to start
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the event producer.

        This method should cleanly shutdown the producer and release any
        resources. Must be idempotent and not raise exceptions.
        """
        pass

    def publish(self, event: "Event") -> None:
        """
        Publish an event to the event bus.

        Args:
            event: Event to publish

        Raises:
            RuntimeError: If no event bus is configured
            ValueError: If event is invalid
        """
        if not self._event_bus:
            raise RuntimeError(f"No event bus configured for producer {self.name}")

        # Import here to avoid circular imports
        from .event import Event

        if not isinstance(event, Event):
            raise ValueError("event must be an instance of Event")

        self._event_bus.publish(event)

    def __str__(self) -> str:
        """String representation of the producer."""
        status = "running" if self.is_running else "stopped"
        return f"{self.__class__.__name__}('{self.name}', {status})"
