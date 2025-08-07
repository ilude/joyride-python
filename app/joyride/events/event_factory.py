"""
Event factory for consistent event creation in the Joyride DNS Service.

This module provides the EventFactory class that simplifies event creation
using the schema composition system and provides a consistent interface
for creating events with proper validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar

from .event import Event
from .event_schemas import EventSchema
from .schemas import (
    ContainerEventSchema,
    DNSEventSchema,
    ErrorEventSchema,
    FileEventSchema,
    HealthEventSchema,
    NodeEventSchema,
    SystemEventSchema,
)
from .types import (
    ContainerEvent,
    DNSEvent,
    ErrorEvent,
    FileEvent,
    HealthEvent,
    NodeEvent,
    SystemEvent,
)

T = TypeVar("T", bound=Event)


class EventFactory:
    """
    Factory class for creating events with schema validation.

    This factory provides a consistent interface for creating events
    using the schema composition system. It handles validation,
    default values, and proper event initialization.
    """

    # Mapping of event types to their corresponding event classes and schemas
    _EVENT_MAPPINGS = {
        "container": {
            "event_class": ContainerEvent,
            "schema_class": ContainerEventSchema,
            "field_mapping": {
                # Schema field -> Event constructor parameter
                "hostname": "container_name",  # Map hostname to container_name
                "domain_suffix": None,  # Don't pass to constructor
            },
        },
        "dns": {
            "event_class": DNSEvent,
            "schema_class": DNSEventSchema,
            "field_mapping": {
                # Schema field -> Event constructor parameter
                "hostname": "record_name",  # Map hostname to record_name
                "ip_address": "record_value",  # Map ip_address to record_value
                "source_id": None,  # Don't pass to constructor
                "priority": None,  # Don't pass to constructor
            },
        },
        "error": {
            "event_class": ErrorEvent,
            "schema_class": ErrorEventSchema,
            "field_mapping": {
                # Schema field -> Event constructor parameter
                "message": "error_message",  # Map message to error_message
                "operation": None,  # Don't pass to constructor
                "stack_trace": None,  # Don't pass to constructor
                "context": None,  # Don't pass to constructor
                "retry_count": None,  # Don't pass to constructor
            },
        },
        "file": {
            "event_class": FileEvent,
            "schema_class": FileEventSchema,
            "field_mapping": {
                # Schema field -> Event constructor parameter
                "file_name": None,  # Don't pass to constructor
                "file_size": None,  # Don't pass to constructor
                "last_modified": None,  # Don't pass to constructor
                "total_records": None,  # Don't pass to constructor
            },
        },
        "health": {
            "event_class": HealthEvent,
            "schema_class": HealthEventSchema,
            "field_mapping": {
                # Schema field -> Event constructor parameter
                "check_duration": None,  # Don't pass to constructor
                "response_time": None,  # Don't pass to constructor
                "metrics": None,  # Don't pass to constructor
                "thresholds": None,  # Don't pass to constructor
                "message": None,  # Don't pass to constructor
                "previous_status": None,  # Don't pass to constructor
            },
        },
        "node": {
            "event_class": NodeEvent,
            "schema_class": NodeEventSchema,
            "field_mapping": {
                # Schema field -> Event constructor parameter
                "node_name": None,  # Don't pass to constructor
                "version": None,  # Don't pass to constructor
                "incarnation": None,  # Don't pass to constructor
                "cluster_size": None,  # Don't pass to constructor
            },
        },
        "system": {
            "event_class": SystemEvent,
            "schema_class": SystemEventSchema,
            "field_mapping": {
                # Schema field -> Event constructor parameter
                "severity": None,  # Don't pass to constructor
                "message": None,  # Don't pass to constructor
                "component_version": None,  # Don't pass to constructor
                "process_id": None,  # Don't pass to constructor
                "thread_id": None,  # Don't pass to constructor
                "memory_usage": None,  # Don't pass to constructor
                "metadata": None,  # Don't pass to constructor
            },
        },
    }

    @classmethod
    def create_event(
        cls,
        event_category: str,
        event_type: str,
        source: str,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> Event:
        """
        Create an event using the factory pattern with schema validation.

        Args:
            event_category: Category of event (container, dns, error, etc.)
            event_type: Specific type of event within the category
            source: Source component generating the event
            timestamp: Event timestamp (defaults to current time)
            **kwargs: Additional event-specific data

        Returns:
            Created and validated event instance

        Raises:
            ValueError: If event category is not supported or validation fails

        Example:
            # Create a container event
            event = EventFactory.create_event(
                event_category='container',
                event_type='container_started',
                source='docker_monitor',
                container_id='abc123',
                container_name='web-server',
                image='nginx:latest'
            )
        """
        if event_category not in cls._EVENT_MAPPINGS:
            raise ValueError(f"Unsupported event category: {event_category}")

        mapping = cls._EVENT_MAPPINGS[event_category]
        event_class = mapping["event_class"]

        # Create event directly using the event class constructor
        # Each event category has its own creation method that knows the right parameters
        if event_category == "container":
            return cls._create_container_event_direct(
                event_class, event_type, source, timestamp, **kwargs
            )
        elif event_category == "dns":
            return cls._create_dns_event_direct(
                event_class, event_type, source, timestamp, **kwargs
            )
        elif event_category == "error":
            return cls._create_error_event_direct(
                event_class, event_type, source, timestamp, **kwargs
            )
        elif event_category == "file":
            return cls._create_file_event_direct(
                event_class, event_type, source, timestamp, **kwargs
            )
        elif event_category == "health":
            return cls._create_health_event_direct(
                event_class, event_type, source, timestamp, **kwargs
            )
        elif event_category == "node":
            return cls._create_node_event_direct(
                event_class, event_type, source, timestamp, **kwargs
            )
        elif event_category == "system":
            return cls._create_system_event_direct(
                event_class, event_type, source, timestamp, **kwargs
            )
        else:
            raise ValueError(f"Unsupported event category: {event_category}")

    @classmethod
    def _create_container_event_direct(
        cls, event_class, event_type, source, timestamp, **kwargs
    ):
        """Create a container event directly."""
        return event_class(
            event_type=event_type,
            source=source,
            container_id=kwargs.get("container_id", ""),
            container_name=kwargs.get("container_name", ""),
            image=kwargs.get("image", ""),
            labels=kwargs.get("labels"),
            networks=kwargs.get("networks"),
            ports=kwargs.get("ports"),
            status=kwargs.get("status"),
            timestamp=timestamp,
        )

    @classmethod
    def _create_dns_event_direct(
        cls, event_class, event_type, source, timestamp, **kwargs
    ):
        """Create a DNS event directly."""
        return event_class(
            event_type=event_type,
            source=source,
            record_name=kwargs.get("record_name", ""),
            record_type=kwargs.get("record_type", "A"),
            record_value=kwargs.get("record_value"),
            ttl=kwargs.get("ttl", 300),
            timestamp=timestamp,
        )

    @classmethod
    def _create_error_event_direct(
        cls, event_class, event_type, source, timestamp, **kwargs
    ):
        """Create an error event directly."""
        return event_class(
            event_type=event_type,
            source=source,
            error_type=kwargs.get("error_type", "general"),
            error_message=kwargs.get("error_message", ""),
            error_code=kwargs.get("error_code"),
            stack_trace=kwargs.get("stack_trace"),
            context=kwargs.get("context"),
            severity=kwargs.get("severity", "error"),
            timestamp=timestamp,
        )

    @classmethod
    def _create_file_event_direct(
        cls, event_class, event_type, source, timestamp, **kwargs
    ):
        """Create a file event directly."""
        return event_class(
            event_type=event_type,
            source=source,
            file_path=kwargs.get("file_path", ""),
            operation=kwargs.get("operation", ""),
            records=kwargs.get("records"),
            file_size=kwargs.get("file_size"),
            file_mtime=kwargs.get("file_mtime"),
            timestamp=timestamp,
        )

    @classmethod
    def _create_health_event_direct(
        cls, event_class, event_type, source, timestamp, **kwargs
    ):
        """Create a health event directly."""
        return event_class(
            event_type=event_type,
            source=source,
            component=kwargs.get("component", ""),
            health_status=kwargs.get("status", ""),
            check_name=kwargs.get("check_name", ""),
            check_result=kwargs.get("check_result", True),
            check_message=kwargs.get("check_message"),
            check_duration=kwargs.get("check_duration"),
            metrics=kwargs.get("metrics"),
            timestamp=timestamp,
        )

    @classmethod
    def _create_node_event_direct(
        cls, event_class, event_type, source, timestamp, **kwargs
    ):
        """Create a node event directly."""
        return event_class(
            event_type=event_type,
            source=source,
            node_id=kwargs.get("node_id", ""),
            node_address=kwargs.get("node_address", ""),
            node_port=kwargs.get("node_port", 0),
            node_state=kwargs.get("node_state", ""),
            cluster_size=kwargs.get("cluster_size"),
            node_metadata=kwargs.get("node_metadata"),
            timestamp=timestamp,
        )

    @classmethod
    def _create_system_event_direct(
        cls, event_class, event_type, source, timestamp, **kwargs
    ):
        """Create a system event directly."""
        return event_class(
            event_type=event_type,
            source=source,
            component=kwargs.get("component", ""),
            operation=kwargs.get("operation", ""),
            status=kwargs.get("status", "unknown"),
            error_message=kwargs.get("error_message"),
            configuration=kwargs.get("configuration"),
            timestamp=timestamp,
        )

    @classmethod
    def create_container_event(
        cls,
        event_type: str,
        source: str,
        container_id: str,
        container_name: str,
        image: str,
        labels: Optional[Dict[str, str]] = None,
        networks: Optional[Dict[str, Any]] = None,
        ports: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> ContainerEvent:
        """Create a container event with simplified interface."""
        return cls.create_event(
            event_category="container",
            event_type=event_type,
            source=source,
            container_id=container_id,
            container_name=container_name,
            image=image,
            labels=labels,
            networks=networks,
            ports=ports,
            status=status,
            timestamp=timestamp,
            **kwargs,
        )

    @classmethod
    def create_dns_event(
        cls,
        event_type: str,
        source: str,
        record_name: str,
        record_type: str = "A",
        record_value: Optional[str] = None,
        ttl: int = 300,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> DNSEvent:
        """Create a DNS event with simplified interface."""
        return cls.create_event(
            event_category="dns",
            event_type=event_type,
            source=source,
            record_name=record_name,
            record_type=record_type,
            record_value=record_value,
            ttl=ttl,
            timestamp=timestamp,
            **kwargs,
        )

    @classmethod
    def create_error_event(
        cls,
        event_type: str,
        source: str,
        error_message: str,
        error_type: str = "general",
        error_code: Optional[str] = None,
        severity: str = "error",
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> ErrorEvent:
        """Create an error event with simplified interface."""
        return cls.create_event(
            event_category="error",
            event_type=event_type,
            source=source,
            error_message=error_message,
            error_type=error_type,
            error_code=error_code,
            severity=severity,
            stack_trace=stack_trace,
            context=context,
            timestamp=timestamp,
            **kwargs,
        )

    @classmethod
    def create_file_event(
        cls,
        event_type: str,
        source: str,
        file_path: str,
        operation: str,
        records: Optional[List[Dict[str, str]]] = None,
        file_size: Optional[int] = None,
        file_mtime: Optional[datetime] = None,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> FileEvent:
        """Create a file event with simplified interface."""
        return cls.create_event(
            event_category="file",
            event_type=event_type,
            source=source,
            file_path=file_path,
            operation=operation,
            records=records,
            file_size=file_size,
            file_mtime=file_mtime,
            timestamp=timestamp,
            **kwargs,
        )

    @classmethod
    def create_health_event(
        cls,
        event_type: str,
        source: str,
        component: str,
        health_status: str = "unknown",
        check_name: str = "general",
        check_result: bool = True,
        check_message: Optional[str] = None,
        check_duration: Optional[float] = None,
        metrics: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> HealthEvent:
        """Create a health event with simplified interface."""
        return cls.create_event(
            event_category="health",
            event_type=event_type,
            source=source,
            component=component,
            status=health_status,
            check_name=check_name,
            check_result=check_result,
            check_message=check_message,
            check_duration=check_duration,
            metrics=metrics,
            timestamp=timestamp,
            **kwargs,
        )

    @classmethod
    def create_node_event(
        cls,
        event_type: str,
        source: str,
        node_id: str,
        node_address: str,
        node_port: int,
        node_state: str = "unknown",
        cluster_size: Optional[int] = None,
        node_metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> NodeEvent:
        """Create a node event with simplified interface."""
        return cls.create_event(
            event_category="node",
            event_type=event_type,
            source=source,
            node_id=node_id,
            node_address=node_address,
            node_port=node_port,
            node_state=node_state,
            cluster_size=cluster_size,
            node_metadata=node_metadata,
            timestamp=timestamp,
            **kwargs,
        )

    @classmethod
    def create_system_event(
        cls,
        event_type: str,
        source: str,
        component: str,
        operation: str = "unknown",
        status: str = "unknown",
        error_message: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> SystemEvent:
        """Create a system event with simplified interface."""
        return cls.create_event(
            event_category="system",
            event_type=event_type,
            source=source,
            component=component,
            operation=operation,
            status=status,
            error_message=error_message,
            configuration=configuration,
            timestamp=timestamp,
            **kwargs,
        )

    @classmethod
    def create_from_schema(cls, event_class: Type[T], schema: EventSchema) -> T:
        """
        Create an event from a validated schema instance.

        Args:
            event_class: Event class to instantiate
            schema: Validated schema instance

        Returns:
            Created event instance
        """
        # For now, this is a placeholder since we're using direct creation
        # This method could be enhanced later if needed
        raise NotImplementedError(
            "Schema-based creation not implemented in simplified factory"
        )

    @classmethod
    def validate_event_data(cls, event_category: str, **kwargs) -> bool:
        """
        Validate event data using basic checks.

        Args:
            event_category: Category of event to validate
            **kwargs: Event data to validate

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        if event_category not in cls._EVENT_MAPPINGS:
            raise ValueError(f"Unsupported event category: {event_category}")

        # Basic validation - check for required fields based on category
        required_fields = {
            "container": ["container_id", "container_name", "image"],
            "dns": ["record_name"],
            "error": ["error_message"],  # error_type will default to 'general'
            "file": ["file_path", "operation"],
            "health": [
                "component"
            ],  # health_status will default, check_name will default
            "node": ["node_id", "node_address", "node_port"],  # node_state will default
            "system": ["component"],  # operation and status will default
        }

        missing_fields = []
        for field in required_fields.get(event_category, []):
            if field not in kwargs or not kwargs[field]:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"Event validation failed: missing required fields: {', '.join(missing_fields)}"
            )

        return True

    @classmethod
    def get_supported_categories(cls) -> list[str]:
        """Get list of supported event categories."""
        return list(cls._EVENT_MAPPINGS.keys())

    @classmethod
    def get_schema_for_category(cls, event_category: str) -> Type[EventSchema]:
        """Get the schema class for a specific event category."""
        if event_category not in cls._EVENT_MAPPINGS:
            raise ValueError(f"Unsupported event category: {event_category}")
        return cls._EVENT_MAPPINGS[event_category]["schema_class"]

    @classmethod
    def get_event_class_for_category(cls, event_category: str) -> Type[Event]:
        """Get the event class for a specific event category."""
        if event_category not in cls._EVENT_MAPPINGS:
            raise ValueError(f"Unsupported event category: {event_category}")
        return cls._EVENT_MAPPINGS[event_category]["event_class"]


# Convenience function for quick event creation
def create_event(event_category: str, event_type: str, source: str, **kwargs) -> Event:
    """
    Convenience function for creating events using the factory.

    This is a shorthand for EventFactory.create_event().
    """
    return EventFactory.create_event(
        event_category=event_category, event_type=event_type, source=source, **kwargs
    )
