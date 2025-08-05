"""
Event subscription management for the Joyride DNS Service.

This module provides subscription handling with activation/deactivation
and event matching capabilities.
"""

from typing import Callable

from ..event_base import JoyrideEvent
from .filter import JoyrideEventFilter


class JoyrideEventSubscription:
    """
    Represents a subscription to events in the Joyride DNS Service.

    Manages the relationship between event filters and handler functions,
    providing activation/deactivation capabilities for dynamic subscription
    management.
    """

    def __init__(
        self,
        handler: Callable[[JoyrideEvent], None],
        event_filter: JoyrideEventFilter,
        subscription_id: str,
    ):
        """
        Initialize event subscription.

        Args:
            handler: Function to handle matching events
            event_filter: Filter for event matching
            subscription_id: Unique identifier for this subscription
        """
        self.handler = handler
        self.event_filter = event_filter
        self.subscription_id = subscription_id
        self.active = True

    def matches(self, event: JoyrideEvent) -> bool:
        """Check if event matches this subscription."""
        return self.active and self.event_filter.matches(event)

    def handle(self, event: JoyrideEvent) -> None:
        """Handle an event if subscription is active."""
        if self.active:
            self.handler(event)

    def deactivate(self) -> None:
        """Deactivate this subscription."""
        self.active = False
