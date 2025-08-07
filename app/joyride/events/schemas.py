"""
Schema definitions for all event types using field descriptors.

This module defines the specific schemas for each event type in the system,
providing declarative field definitions with validation and default values.
"""

from .event_schemas import EventSchema
from .fields import DictField, IntField, StringField


class ContainerEventSchema(EventSchema):
    """Schema for Docker container events."""

    # Core container identification
    container_id = StringField(data_key="container_id", min_length=1, max_length=64)
    container_name = StringField(
        data_key="container_name", min_length=1, max_length=255
    )

    # Event details
    event_type = StringField(data_key="event_type")
    timestamp = IntField(data_key="timestamp")

    # Container configuration
    image = StringField(data_key="image", default="", max_length=512)
    labels = DictField(data_key="labels", default={})

    # DNS-related fields
    hostname = StringField(data_key="hostname", default="", max_length=253)
    domain_suffix = StringField(
        data_key="domain_suffix", default=".internal", max_length=100
    )


class DNSEventSchema(EventSchema):
    """Schema for DNS record events."""

    # DNS record identification
    hostname = StringField(data_key="hostname", min_length=1, max_length=253)
    record_type = StringField(data_key="record_type")

    # Event details
    event_type = StringField(data_key="event_type")
    timestamp = IntField(data_key="timestamp")

    # DNS record data
    ip_address = StringField(data_key="ip_address")
    ttl = IntField(data_key="ttl", default=300)

    # Source information
    source = StringField(data_key="source")
    source_id = StringField(data_key="source_id", default="", max_length=255)

    # Metadata
    priority = IntField(data_key="priority", default=0)


class FileEventSchema(EventSchema):
    """Schema for hosts file events."""

    # File identification
    file_path = StringField(data_key="file_path", min_length=1, max_length=4096)
    file_name = StringField(data_key="file_name", min_length=1, max_length=255)

    # Event details
    event_type = StringField(data_key="event_type")
    timestamp = IntField(data_key="timestamp")

    # File metadata
    file_size = IntField(data_key="file_size", default=0)
    last_modified = IntField(data_key="last_modified", default=0)

    # Content analysis
    total_records = IntField(data_key="total_records", default=0)


class NodeEventSchema(EventSchema):
    """Schema for SWIM cluster node events."""

    # Node identification
    node_id = StringField(data_key="node_id", min_length=1, max_length=128)
    node_address = StringField(data_key="node_address")
    node_port = IntField(data_key="node_port")

    # Event details
    event_type = StringField(data_key="event_type")
    timestamp = IntField(data_key="timestamp")

    # Node metadata
    node_name = StringField(data_key="node_name", default="", max_length=255)
    version = StringField(data_key="version", default="", max_length=50)

    # Cluster state
    incarnation = IntField(data_key="incarnation", default=0)
    cluster_size = IntField(data_key="cluster_size", default=1)


class SystemEventSchema(EventSchema):
    """Schema for system lifecycle events."""

    # Event identification
    event_type = StringField(data_key="event_type")
    timestamp = IntField(data_key="timestamp")

    # Component information
    component = StringField(data_key="component", min_length=1, max_length=100)
    component_version = StringField(
        data_key="component_version", default="", max_length=50
    )

    # Event details
    severity = StringField(data_key="severity")
    message = StringField(data_key="message", max_length=1000)

    # Context information
    process_id = IntField(data_key="process_id", default=0)
    thread_id = IntField(data_key="thread_id", default=0)
    memory_usage = IntField(data_key="memory_usage", default=0)

    # Additional data
    metadata = DictField(data_key="metadata", default={})


class ErrorEventSchema(EventSchema):
    """Schema for error events."""

    # Error identification
    error_code = StringField(data_key="error_code", min_length=1, max_length=50)
    error_type = StringField(data_key="error_type", min_length=1, max_length=100)
    timestamp = IntField(data_key="timestamp")

    # Error details
    message = StringField(data_key="message", max_length=1000)
    severity = StringField(data_key="severity")

    # Context information
    component = StringField(data_key="component", min_length=1, max_length=100)
    operation = StringField(data_key="operation", default="", max_length=100)

    # Stack trace and debugging
    stack_trace = StringField(data_key="stack_trace", default="", max_length=10000)
    context = DictField(data_key="context", default={})

    # Recovery information
    retry_count = IntField(data_key="retry_count", default=0)


class HealthEventSchema(EventSchema):
    """Schema for health check events."""

    # Health check identification
    check_name = StringField(data_key="check_name", min_length=1, max_length=100)
    component = StringField(data_key="component", min_length=1, max_length=100)
    timestamp = IntField(data_key="timestamp")

    # Health status
    status = StringField(data_key="status")
    previous_status = StringField(data_key="previous_status", default="unknown")

    # Check details
    check_duration = IntField(data_key="check_duration")
    response_time = IntField(data_key="response_time", default=0)

    # Health metrics
    metrics = DictField(data_key="metrics", default={})
    thresholds = DictField(data_key="thresholds", default={})

    # Additional information
    message = StringField(data_key="message", default="", max_length=500)
    details = DictField(data_key="details", default={})
