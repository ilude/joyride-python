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

# Event factory
from .event_factory import EventFactory, create_event

# Registry system
from .event_filter import EventFilter
from .event_handler import EventHandler
from .event_producer import EventProducer
from .event_registry import EventRegistry, get_event_registry, reset_event_registry

# Event schemas
from .event_schemas import EventSchema, SchemaFactory, SchemaField, SchemaValidator
from .event_subscription import EventSubscription

# Field descriptors
from .fields import (
    ChoiceField,
    DictField,
    EventField,
    IntField,
    OptionalField,
    StringField,
)
from .schemas import (
    ContainerEventSchema,
    DNSEventSchema,
    ErrorEventSchema,
    FileEventSchema,
    HealthEventSchema,
    NodeEventSchema,
    SystemEventSchema,
)

# Event types
from .types import (
    ContainerEvent,
    DNSEvent,
    ErrorEvent,
    FileEvent,
    HealthEvent,
    NodeEvent,
    SystemEvent,
)

# Validation mixins
from .validation_mixins import (
    DNS_RECORD_TYPE_VALIDATOR,
    ERROR_SEVERITY_VALIDATOR,
    HEALTH_STATUS_VALIDATOR,
    HOSTNAME_VALIDATOR,
    IPV4_VALIDATOR,
    NON_EMPTY_STRING_VALIDATOR,
    NON_NEGATIVE_INTEGER_VALIDATOR,
    POSITIVE_INTEGER_VALIDATOR,
    ChoiceValidator,
    CompositeValidator,
    IPAddressValidator,
    NumericValidator,
    StringValidator,
    ValidationMixin,
)

__all__ = [
    # Event system classes
    "Event",
    "EventHandler",
    "EventProducer",
    "EventBus",
    # Field descriptors
    "EventField",
    "StringField",
    "IntField",
    "ChoiceField",
    "DictField",
    "OptionalField",
    # Validation mixins
    "ValidationMixin",
    "StringValidator",
    "NumericValidator",
    "ChoiceValidator",
    "IPAddressValidator",
    "CompositeValidator",
    # Predefined validators
    "DNS_RECORD_TYPE_VALIDATOR",
    "HEALTH_STATUS_VALIDATOR",
    "ERROR_SEVERITY_VALIDATOR",
    "POSITIVE_INTEGER_VALIDATOR",
    "NON_NEGATIVE_INTEGER_VALIDATOR",
    "NON_EMPTY_STRING_VALIDATOR",
    "HOSTNAME_VALIDATOR",
    "IPV4_VALIDATOR",
    # Event schemas
    "EventSchema",
    "SchemaField",
    "SchemaFactory",
    "SchemaValidator",
    "ContainerEventSchema",
    "DNSEventSchema",
    "ErrorEventSchema",
    "FileEventSchema",
    "HealthEventSchema",
    "NodeEventSchema",
    "SystemEventSchema",
    # Event factory
    "EventFactory",
    "create_event",
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
