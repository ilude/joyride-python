"""
Event system package for the Joyride DNS Service.

This package provides a comprehensive event system with Joyride-prefixed
classes to avoid naming conflicts with standard library or third-party modules.

The event system follows the Observer pattern and provides both
synchronous and filtered event processing capabilities.
"""

# Event bus
from .bus import JoyrideEventBus

# Core event system
from .event_base import JoyrideEvent
from .event_handler import JoyrideEventHandler
from .event_producer import JoyrideEventProducer

# Registry system
from .registry import JoyrideEventFilter, JoyrideEventRegistry, JoyrideEventSubscription

# Event types
from .types import (
    JoyrideContainerEvent,
    JoyrideDNSEvent,
    JoyrideErrorEvent,
    JoyrideFileEvent,
    JoyrideHealthEvent,
    JoyrideNodeEvent,
    JoyrideSystemEvent,
)

__all__ = [
    # Core classes
    "JoyrideEvent",
    "JoyrideEventHandler",
    "JoyrideEventProducer",
    "JoyrideEventBus",
    # Registry system
    "JoyrideEventFilter",
    "JoyrideEventRegistry",
    "JoyrideEventSubscription",
    # Event types
    "JoyrideContainerEvent",
    "JoyrideDNSEvent",
    "JoyrideErrorEvent",
    "JoyrideFileEvent",
    "JoyrideHealthEvent",
    "JoyrideNodeEvent",
    "JoyrideSystemEvent",
]
