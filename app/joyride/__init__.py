"""
Joyride DNS Service core package.

This package contains the core components of the Joyride DNS Service
including the event system, dependency injection, and other core utilities.
"""

# Re-export events for backward compatibility
from .events import *

# Note: injection imports are available but not auto-imported to avoid dependency issues
# Use: from app.joyride.injection import ... for injection functionality

__all__ = [
    # Event system classes
    "JoyrideEvent",
    "JoyrideEventHandler",
    "JoyrideEventProducer",
    "JoyrideEventBus",
    # Registry system
    "JoyrideEventFilter",
    "JoyrideEventRegistry",
    "JoyrideEventSubscription",
    "get_joyride_registry",
    "reset_joyride_registry",
    # Event types
    "JoyrideContainerEvent",
    "JoyrideDNSEvent",
    "JoyrideErrorEvent",
    "JoyrideFileEvent",
    "JoyrideHealthEvent",
    "JoyrideNodeEvent",
    "JoyrideSystemEvent",
]