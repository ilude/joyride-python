"""
Event registry system for the Joyride DNS Service.

This module provides centralized event type registration and subscription
management with thread-safe operations and pattern-based filtering.
"""

import threading
from typing import Any, Callable, Dict, List, Optional, Type

from ..core.event_base import JoyrideEvent
from .filter import JoyrideEventFilter
from .subscription import JoyrideEventSubscription


class JoyrideEventRegistry:
    """
    Central registry for event types and subscriptions in the Joyride DNS Service.

    Provides thread-safe management of event type registration and subscription
    handling with support for pattern-based filtering and dynamic subscription
    management.
    """

    def __init__(self):
        """Initialize the event registry."""
        self._event_types: Dict[str, Type[JoyrideEvent]] = {}
        self._subscriptions: Dict[str, JoyrideEventSubscription] = {}
        self._lock = threading.RLock()
        self._subscription_counter = 0

    def register_event_type(self, event_class: Type[JoyrideEvent]) -> None:
        """
        Register an event type in the registry.

        Args:
            event_class: Event class to register

        Raises:
            ValueError: If event class is invalid or already registered
        """
        if not issubclass(event_class, JoyrideEvent):
            raise ValueError(
                f"Event class {event_class} must inherit from JoyrideEvent"
            )

        class_name = event_class.__name__

        with self._lock:
            if class_name in self._event_types:
                if self._event_types[class_name] != event_class:
                    raise ValueError(
                        f"Event type {class_name} already registered with different class"
                    )
                # Same class, no need to re-register
                return

            self._event_types[class_name] = event_class

    def get_event_type(self, event_type_name: str) -> Optional[Type[JoyrideEvent]]:
        """
        Get registered event type by name.

        Args:
            event_type_name: Name of the event type

        Returns:
            Event class if registered, None otherwise
        """
        with self._lock:
            return self._event_types.get(event_type_name)

    def list_event_types(self) -> List[str]:
        """
        Get list of all registered event type names.

        Returns:
            List of registered event type names
        """
        with self._lock:
            return list(self._event_types.keys())

    def subscribe(
        self,
        handler: Callable[[JoyrideEvent], None],
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        pattern: Optional[str] = None,
        custom_filter: Optional[Callable[[JoyrideEvent], bool]] = None,
    ) -> str:
        """
        Subscribe to events with optional filtering.

        Args:
            handler: Function to call when matching events occur
            event_type: Exact event type to match
            source: Exact source to match
            pattern: Wildcard pattern for event types (e.g., "dns.*", "container.started")
            custom_filter: Custom filtering function

        Returns:
            Subscription ID for managing the subscription

        Raises:
            ValueError: If no filter criteria provided or handler is invalid
        """
        if not callable(handler):
            raise ValueError("Handler must be callable")

        if not any([event_type, source, pattern, custom_filter]):
            raise ValueError("At least one filter criterion must be provided")

        event_filter = JoyrideEventFilter(
            event_type=event_type,
            source=source,
            pattern=pattern,
            custom_filter=custom_filter,
        )

        with self._lock:
            self._subscription_counter += 1
            subscription_id = f"sub_{self._subscription_counter}"

            subscription = JoyrideEventSubscription(
                handler=handler,
                event_filter=event_filter,
                subscription_id=subscription_id,
            )

            self._subscriptions[subscription_id] = subscription

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Remove a subscription.

        Args:
            subscription_id: ID of subscription to remove

        Returns:
            True if subscription was found and removed
        """
        with self._lock:
            subscription = self._subscriptions.get(subscription_id)
            if subscription:
                subscription.deactivate()
                del self._subscriptions[subscription_id]
                return True
            return False

    def get_matching_subscriptions(
        self, event: JoyrideEvent
    ) -> List[JoyrideEventSubscription]:
        """
        Get all subscriptions that match the given event.

        Args:
            event: Event to match against subscriptions

        Returns:
            List of matching active subscriptions
        """
        matching = []

        with self._lock:
            for subscription in self._subscriptions.values():
                if subscription.matches(event):
                    matching.append(subscription)

        return matching

    def get_subscription_count(self) -> int:
        """
        Get the total number of active subscriptions.

        Returns:
            Number of active subscriptions
        """
        with self._lock:
            return len([s for s in self._subscriptions.values() if s.active])

    def clear_subscriptions(self) -> None:
        """Remove all subscriptions."""
        with self._lock:
            for subscription in self._subscriptions.values():
                subscription.deactivate()
            self._subscriptions.clear()

    def get_subscription_info(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a subscription.

        Args:
            subscription_id: ID of subscription

        Returns:
            Dictionary with subscription info or None if not found
        """
        with self._lock:
            subscription = self._subscriptions.get(subscription_id)
            if not subscription:
                return None

            return {
                "subscription_id": subscription.subscription_id,
                "active": subscription.active,
                "filter": str(subscription.event_filter),
                "handler": subscription.handler.__name__
                if hasattr(subscription.handler, "__name__")
                else str(subscription.handler),
            }


# Global registry instance
_global_registry: Optional[JoyrideEventRegistry] = None
_registry_lock = threading.Lock()


def get_joyride_registry() -> JoyrideEventRegistry:
    """
    Get the global Joyride event registry instance.

    Returns:
        Global JoyrideEventRegistry instance
    """
    global _global_registry

    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = JoyrideEventRegistry()

    return _global_registry


def reset_joyride_registry() -> None:
    """Reset the global registry (mainly for testing)."""
    global _global_registry

    with _registry_lock:
        _global_registry = None
