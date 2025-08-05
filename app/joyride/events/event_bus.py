"""
Event Bus implementation for the Joyride DNS Service.

Provides centralized event management using the event system.
"""

import logging
import threading
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Type

if TYPE_CHECKING:
    from .event import Event
    from .handler import EventHandler

from .event_subscription import EventSubscription
from .registry import EventRegistry

logger = logging.getLogger(__name__)


class EventBus:
    """
    Centralized event bus for managing event distribution.

    Provides thread-safe event publishing and subscription management
    using the Joyride event system.
    """

    def __init__(self) -> None:
        """Initialize the event bus with registry and threading support."""
        self._registry = EventRegistry()
        self._lock = threading.RLock()
        self._handlers: Dict[Type["Event"], Set["EventHandler"]] = {}
        self._is_active = True
        self._event_count = 0
        logger.info("EventBus initialized")

    def subscribe(
        self,
        event_type: Type["Event"],
        handler: "EventHandler",
        filter_pattern: Optional[str] = None,
    ) -> "EventSubscription":
        """
        Subscribe a handler to events of a specific type.

        Args:
            event_type: The type of event to subscribe to
            handler: The handler to call when events occur
            filter_pattern: Optional regex pattern for event filtering

        Returns:
            Subscription object that can be used to unsubscribe
        """
        with self._lock:
            if not self._is_active:
                raise RuntimeError("EventBus is not active")

            # Add to direct handler mapping for efficiency
            if event_type not in self._handlers:
                self._handlers[event_type] = set()
            self._handlers[event_type].add(handler)

            # Create subscription through registry for filtering
            subscription = self._registry.subscribe(event_type, handler, filter_pattern)

            logger.debug(
                f"Handler {handler.__class__.__name__} subscribed to {event_type.__name__}"
            )
            return subscription

    def unsubscribe(self, subscription: "EventSubscription") -> bool:
        """
        Unsubscribe a handler using its subscription.

        Args:
            subscription: The subscription to remove

        Returns:
            True if successfully unsubscribed, False otherwise
        """
        with self._lock:
            success = self._registry.unsubscribe(subscription)

            # Also remove from direct handler mapping
            if success:
                event_type = subscription.event_type
                handler = subscription.handler

                if event_type in self._handlers:
                    self._handlers[event_type].discard(handler)
                    if not self._handlers[event_type]:
                        del self._handlers[event_type]

                logger.debug(
                    f"Handler {handler.__class__.__name__} unsubscribed from {event_type.__name__}"
                )

            return success

    def publish(self, event: "Event") -> int:
        """
        Publish an event to all subscribed handlers.

        Args:
            event: The event to publish

        Returns:
            Number of handlers that processed the event
        """
        if not self._is_active:
            logger.warning("Attempted to publish event on inactive bus")
            return 0

        with self._lock:
            self._event_count += 1
            event_type = type(event)
            processed_count = 0

            # Get matching subscriptions from registry (includes filtering)
            subscriptions = self._registry.get_matching_subscriptions(event)

            for subscription in subscriptions:
                try:
                    subscription.handler.handle(event)
                    processed_count += 1
                except Exception as e:
                    logger.error(
                        f"Error handling event {event_type.__name__} "
                        f"with handler {subscription.handler.__class__.__name__}: {e}"
                    )

            logger.debug(
                f"Published {event_type.__name__} to {processed_count} handlers"
            )
            return processed_count

    def get_subscriptions(
        self, event_type: Optional[Type["Event"]] = None
    ) -> List["EventSubscription"]:
        """
        Get all subscriptions, optionally filtered by event type.

        Args:
            event_type: Optional event type to filter by

        Returns:
            List of matching subscriptions
        """
        with self._lock:
            return self._registry.get_subscriptions(event_type)

    def clear_subscriptions(
        self, event_type: Optional[Type["Event"]] = None
    ) -> int:
        """
        Clear subscriptions, optionally filtered by event type.

        Args:
            event_type: Optional event type to clear, if None clears all

        Returns:
            Number of subscriptions cleared
        """
        with self._lock:
            count = self._registry.clear_subscriptions(event_type)

            if event_type is None:
                self._handlers.clear()
            elif event_type in self._handlers:
                del self._handlers[event_type]

            logger.info(f"Cleared {count} subscriptions")
            return count

    def shutdown(self) -> None:
        """Shutdown the event bus and clear all subscriptions."""
        with self._lock:
            if not self._is_active:
                return

            self._is_active = False
            count = self.clear_subscriptions()
            logger.info(f"EventBus shutdown complete, cleared {count} subscriptions")

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the event bus.

        Returns:
            Dictionary with event bus statistics
        """
        with self._lock:
            return {
                "total_events_published": self._event_count,
                "active_event_types": len(self._handlers),
                "total_subscriptions": len(self._registry.get_subscriptions()),
                "is_active": self._is_active,
            }

    @property
    def is_active(self) -> bool:
        """Check if the event bus is active."""
        return self._is_active
