"""
Joyride DNS Service core package.

This package contains the core components of the Joyride DNS Service
including the event system, dependency injection, and other core utilities.
"""

# Re-export events for backward compatibility
from .events import (
    ContainerEvent,
    DNSEvent,
    ErrorEvent,
    Event,
    EventBus,
    EventFilter,
    EventHandler,
    EventProducer,
    EventRegistry,
    EventSubscription,
    FileEvent,
    HealthEvent,
    NodeEvent,
    SystemEvent,
    get_event_registry,
    reset_event_registry,
)

# Note: injection imports are available but not auto-imported to avoid dependency issues
# Use: from app.joyride.injection import ... for injection functionality

__all__ = [
    # Event system classes
    "Event",
    "EventHandler",
    "EventProducer",
    "EventBus",
    # Registry system
    "EventFilter",
    "EventRegistry",
    "EventSubscription",
    "get_event_registry",
    "reset_event_registry",
    # Event types
    "ContainerEvent",
    "DNSEvent",
    "ErrorEvent",
    "FileEvent",
    "HealthEvent",
    "NodeEvent",
    "SystemEvent",
]
