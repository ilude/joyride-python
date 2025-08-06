"""
Event system package for the Joyride DNS Service.

This package provides a comprehensive event system with Joyride-prefixed
classes to avoid naming conflicts with standard library or third-party modules.

The event system follows the Observer pattern and provides both
synchronous and filtered event processing capabilities.
"""

# Core event system
from .event import Event
# Event bus
from .event_bus import EventBus
# Registry system
from .event_filter import EventFilter
from .event_handler import EventHandler
from .event_producer import EventProducer
from .event_registry import (EventRegistry, get_event_registry,
                             reset_event_registry)
from .event_subscription import EventSubscription
# Event types
from .types import (ContainerEvent, DNSEvent, ErrorEvent, FileEvent,
                    HealthEvent, NodeEvent, SystemEvent)

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
