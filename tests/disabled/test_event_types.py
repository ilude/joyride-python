"""
Unit tests for event type definitions.

Tests all concrete event classes to ensure they properly inherit from JoyrideEvent
and provide the expected properties and functionality.
"""

from datetime import datetime, timezone

import pytest

from app.events.types import (
    JoyrideContainerEvent,
    JoyrideDNSEvent,
    JoyrideErrorEvent,
    JoyrideFileEvent,
    JoyrideHealthEvent,
    JoyrideNodeEvent,
    JoyrideSystemEvent,
)


class TestDNSEvent:
    """Test JoyrideDNSEvent class."""

    def test_dns_event_creation_minimal(self):
        """Test creating DNS event with minimal parameters."""
        event = JoyrideDNSEvent(
            event_type="dns.record.added",
            source="test.source",
            record_name="test.example.com",
        )

        assert event.event_type == "dns.record.added"
        assert event.source == "test.source"
        assert event.record_name == "test.example.com"
        assert event.record_type == "A"
        assert event.record_value is None
        assert event.ttl == 300

    def test_dns_event_creation_full(self):
        """Test creating DNS event with all parameters."""
        timestamp = datetime.now(timezone.utc)
        metadata = {"priority": "high"}

        event = JoyrideDNSEvent(
            event_type="dns.record.updated",
            source="dns.handler",
            record_name="api.example.com",
            record_type="AAAA",
            record_value="2001:db8::1",
            ttl=600,
            data={"zone": "example.com"},
            metadata=metadata,
            timestamp=timestamp,
        )

        assert event.event_type == "dns.record.updated"
        assert event.source == "dns.handler"
        assert event.record_name == "api.example.com"
        assert event.record_type == "AAAA"
        assert event.record_value == "2001:db8::1"
        assert event.ttl == 600
        assert event.data["zone"] == "example.com"
        assert event.metadata == metadata
        assert event.timestamp == timestamp

    def test_dns_event_properties(self):
        """Test DNS event property access."""
        event = JoyrideDNSEvent(
            event_type="dns.record.removed",
            source="cleanup.service",
            record_name="old.example.com",
            record_type="CNAME",
            record_value="new.example.com",
            ttl=1800,
        )

        # Test property access
        assert event.record_name == "old.example.com"
        assert event.record_type == "CNAME"
        assert event.record_value == "new.example.com"
        assert event.ttl == 1800

        # Test that properties come from data
        assert event.data["record_name"] == "old.example.com"
        assert event.data["record_type"] == "CNAME"
        assert event.data["record_value"] == "new.example.com"
        assert event.data["ttl"] == 1800

    def test_dns_event_validation_empty_record_name(self):
        """Test DNS event validation with empty record name."""
        with pytest.raises(ValueError, match="DNS record name cannot be empty"):
            JoyrideDNSEvent(
                event_type="dns.record.added", source="test.source", record_name=""
            )

    def test_dns_event_validation_empty_record_type(self):
        """Test DNS event validation with empty record type."""
        with pytest.raises(ValueError, match="DNS record type cannot be empty"):
            JoyrideDNSEvent(
                event_type="dns.record.added",
                source="test.source",
                record_name="test.com",
                record_type="",
            )

    def test_dns_event_validation_negative_ttl(self):
        """Test DNS event validation with negative TTL."""
        with pytest.raises(ValueError, match="DNS record TTL must be non-negative"):
            JoyrideDNSEvent(
                event_type="dns.record.added",
                source="test.source",
                record_name="test.com",
                ttl=-1,
            )


class TestContainerEvent:
    """Test JoyrideContainerEvent class."""

    def test_container_event_creation_minimal(self):
        """Test creating container event with minimal parameters."""
        event = JoyrideContainerEvent(
            event_type="container.started",
            source="docker.monitor",
            container_id="abc123",
            container_name="test-container",
            image="nginx:latest",
        )

        assert event.event_type == "container.started"
        assert event.source == "docker.monitor"
        assert event.container_id == "abc123"
        assert event.container_name == "test-container"
        assert event.image == "nginx:latest"
        assert event.labels == {}
        assert event.networks == {}
        assert event.ports == {}
        assert event.status is None

    def test_container_event_creation_full(self):
        """Test creating container event with all parameters."""
        labels = {"env": "production", "service": "web"}
        networks = {"bridge": {"ip": "172.17.0.2"}}
        ports = {"80/tcp": [{"HostPort": "8080"}]}

        event = JoyrideContainerEvent(
            event_type="container.discovered",
            source="docker.scanner",
            container_id="def456",
            container_name="web-server",
            image="nginx:1.21",
            labels=labels,
            networks=networks,
            ports=ports,
            status="running",
            data={"uptime": "2 days"},
        )

        assert event.container_id == "def456"
        assert event.container_name == "web-server"
        assert event.image == "nginx:1.21"
        assert event.labels == labels
        assert event.networks == networks
        assert event.ports == ports
        assert event.status == "running"
        assert event.data["uptime"] == "2 days"

    def test_container_event_properties(self):
        """Test container event property access."""
        event = JoyrideContainerEvent(
            event_type="container.stopped",
            source="docker.monitor",
            container_id="ghi789",
            container_name="db-container",
            image="postgres:13",
            status="exited",
        )

        # Test property access
        assert event.container_id == "ghi789"
        assert event.container_name == "db-container"
        assert event.image == "postgres:13"
        assert event.status == "exited"

        # Test that properties come from data
        assert event.data["container_id"] == "ghi789"
        assert event.data["container_name"] == "db-container"
        assert event.data["image"] == "postgres:13"
        assert event.data["status"] == "exited"

    def test_container_event_validation_empty_container_id(self):
        """Test container event validation with empty container ID."""
        with pytest.raises(ValueError, match="Container ID cannot be empty"):
            JoyrideContainerEvent(
                event_type="container.started",
                source="docker.monitor",
                container_id="",
                container_name="test",
                image="nginx",
            )

    def test_container_event_validation_empty_container_name(self):
        """Test container event validation with empty container name."""
        with pytest.raises(ValueError, match="Container name cannot be empty"):
            JoyrideContainerEvent(
                event_type="container.started",
                source="docker.monitor",
                container_id="abc123",
                container_name="",
                image="nginx",
            )

    def test_container_event_validation_empty_image(self):
        """Test container event validation with empty image."""
        with pytest.raises(ValueError, match="Container image cannot be empty"):
            JoyrideContainerEvent(
                event_type="container.started",
                source="docker.monitor",
                container_id="abc123",
                container_name="test",
                image="",
            )


class TestNodeEvent:
    """Test JoyrideNodeEvent class."""

    def test_node_event_creation_minimal(self):
        """Test creating node event with minimal parameters."""
        event = JoyrideNodeEvent(
            event_type="node.joined",
            source="swim.protocol",
            node_id="node-001",
            node_address="192.168.1.10",
            node_port=7946,
            node_state="alive",
        )

        assert event.event_type == "node.joined"
        assert event.source == "swim.protocol"
        assert event.node_id == "node-001"
        assert event.node_address == "192.168.1.10"
        assert event.node_port == 7946
        assert event.node_state == "alive"
        assert event.cluster_size is None
        assert event.node_metadata == {}

    def test_node_event_creation_full(self):
        """Test creating node event with all parameters."""
        node_metadata = {"version": "1.0.0", "region": "us-west-2"}

        event = JoyrideNodeEvent(
            event_type="node.suspected",
            source="swim.failure.detector",
            node_id="node-002",
            node_address="192.168.1.11",
            node_port=7946,
            node_state="suspected",
            cluster_size=5,
            node_metadata=node_metadata,
            data={"suspicion_count": 3},
        )

        assert event.node_id == "node-002"
        assert event.node_address == "192.168.1.11"
        assert event.node_port == 7946
        assert event.node_state == "suspected"
        assert event.cluster_size == 5
        assert event.node_metadata == node_metadata
        assert event.data["suspicion_count"] == 3

    def test_node_event_properties(self):
        """Test node event property access."""
        event = JoyrideNodeEvent(
            event_type="node.failed",
            source="swim.protocol",
            node_id="node-003",
            node_address="192.168.1.12",
            node_port=7946,
            node_state="failed",
            cluster_size=4,
        )

        # Test property access
        assert event.node_id == "node-003"
        assert event.node_address == "192.168.1.12"
        assert event.node_port == 7946
        assert event.node_state == "failed"
        assert event.cluster_size == 4

        # Test that properties come from data
        assert event.data["node_id"] == "node-003"
        assert event.data["node_address"] == "192.168.1.12"
        assert event.data["node_port"] == 7946
        assert event.data["node_state"] == "failed"
        assert event.data["cluster_size"] == 4


class TestFileEvent:
    """Test JoyrideFileEvent class."""

    def test_file_event_creation_minimal(self):
        """Test creating file event with minimal parameters."""
        event = JoyrideFileEvent(
            event_type="file.changed",
            source="hosts.monitor",
            file_path="/etc/hosts",
            operation="modified",
        )

        assert event.event_type == "file.changed"
        assert event.source == "hosts.monitor"
        assert event.file_path == "/etc/hosts"
        assert event.operation == "modified"
        assert event.records == []
        assert event.file_size is None
        assert event.file_mtime is None

    def test_file_event_creation_full(self):
        """Test creating file event with all parameters."""
        records = [
            {"hostname": "api.local", "ip": "192.168.1.100"},
            {"hostname": "db.local", "ip": "192.168.1.101"},
        ]
        file_mtime = datetime.now(timezone.utc)

        event = JoyrideFileEvent(
            event_type="file.scanned",
            source="hosts.scanner",
            file_path="/opt/hosts/services.txt",
            operation="scanned",
            records=records,
            file_size=1024,
            file_mtime=file_mtime,
            data={"encoding": "utf-8"},
        )

        assert event.file_path == "/opt/hosts/services.txt"
        assert event.operation == "scanned"
        assert event.records == records
        assert event.file_size == 1024
        assert event.file_mtime == file_mtime
        assert event.data["encoding"] == "utf-8"

    def test_file_event_properties(self):
        """Test file event property access."""
        records = [{"hostname": "test.local", "ip": "127.0.0.1"}]

        event = JoyrideFileEvent(
            event_type="file.created",
            source="hosts.watcher",
            file_path="/tmp/test_hosts",
            operation="created",
            records=records,
            file_size=256,
        )

        # Test property access
        assert event.file_path == "/tmp/test_hosts"
        assert event.operation == "created"
        assert event.records == records
        assert event.file_size == 256

        # Test that properties come from data
        assert event.data["file_path"] == "/tmp/test_hosts"
        assert event.data["operation"] == "created"
        assert event.data["records"] == records
        assert event.data["file_size"] == 256


class TestSystemEvent:
    """Test JoyrideSystemEvent class."""

    def test_system_event_creation_minimal(self):
        """Test creating system event with minimal parameters."""
        event = JoyrideSystemEvent(
            event_type="system.component.started",
            source="bootstrap.runner",
            component="dns.server",
            operation="start",
            status="success",
        )

        assert event.event_type == "system.component.started"
        assert event.source == "bootstrap.runner"
        assert event.component == "dns.server"
        assert event.operation == "start"
        assert event.status == "success"
        assert event.error_message is None
        assert event.configuration == {}

    def test_system_event_creation_full(self):
        """Test creating system event with all parameters."""
        configuration = {"port": 53, "bind_address": "0.0.0.0"}

        event = JoyrideSystemEvent(
            event_type="system.component.failed",
            source="health.monitor",
            component="docker.monitor",
            operation="health_check",
            status="failed",
            error_message="Connection refused",
            configuration=configuration,
            data={"retry_count": 3},
        )

        assert event.component == "docker.monitor"
        assert event.operation == "health_check"
        assert event.status == "failed"
        assert event.error_message == "Connection refused"
        assert event.configuration == configuration
        assert event.data["retry_count"] == 3

    def test_system_event_properties(self):
        """Test system event property access."""
        event = JoyrideSystemEvent(
            event_type="system.config.reloaded",
            source="config.watcher",
            component="event.bus",
            operation="reload",
            status="success",
        )

        # Test property access
        assert event.component == "event.bus"
        assert event.operation == "reload"
        assert event.status == "success"

        # Test that properties come from data
        assert event.data["component"] == "event.bus"
        assert event.data["operation"] == "reload"
        assert event.data["status"] == "success"


class TestErrorEvent:
    """Test JoyrideErrorEvent class."""

    def test_error_event_creation_minimal(self):
        """Test creating error event with minimal parameters."""
        event = JoyrideErrorEvent(
            event_type="error.network.timeout",
            source="docker.client",
            error_type="NetworkTimeout",
            error_message="Connection timed out after 30 seconds",
        )

        assert event.event_type == "error.network.timeout"
        assert event.source == "docker.client"
        assert event.error_type == "NetworkTimeout"
        assert event.error_message == "Connection timed out after 30 seconds"
        assert event.error_code is None
        assert event.stack_trace is None
        assert event.context == {}
        assert event.severity == "error"

    def test_error_event_creation_full(self):
        """Test creating error event with all parameters."""
        context = {"host": "localhost", "port": 2376}
        stack_trace = "Traceback (most recent call last):\n  File..."

        event = JoyrideErrorEvent(
            event_type="error.api.connection",
            source="swim.client",
            error_type="ConnectionError",
            error_message="Failed to connect to SWIM node",
            error_code="CONN_001",
            stack_trace=stack_trace,
            context=context,
            severity="critical",
            data={"attempt": 5},
        )

        assert event.error_type == "ConnectionError"
        assert event.error_message == "Failed to connect to SWIM node"
        assert event.error_code == "CONN_001"
        assert event.stack_trace == stack_trace
        assert event.context == context
        assert event.severity == "critical"
        assert event.data["attempt"] == 5

    def test_error_event_properties(self):
        """Test error event property access."""
        event = JoyrideErrorEvent(
            event_type="error.validation.failed",
            source="dns.validator",
            error_type="ValidationError",
            error_message="Invalid hostname format",
            severity="warning",
        )

        # Test property access
        assert event.error_type == "ValidationError"
        assert event.error_message == "Invalid hostname format"
        assert event.severity == "warning"

        # Test that properties come from data
        assert event.data["error_type"] == "ValidationError"
        assert event.data["error_message"] == "Invalid hostname format"
        assert event.data["severity"] == "warning"

    def test_error_event_validation_empty_error_type(self):
        """Test error event validation with empty error type."""
        with pytest.raises(ValueError, match="Error type cannot be empty"):
            JoyrideErrorEvent(
                event_type="error.test",
                source="test.source",
                error_type="",
                error_message="Test error",
            )

    def test_error_event_validation_empty_error_message(self):
        """Test error event validation with empty error message."""
        with pytest.raises(ValueError, match="Error message cannot be empty"):
            JoyrideErrorEvent(
                event_type="error.test",
                source="test.source",
                error_type="TestError",
                error_message="",
            )

    def test_error_event_validation_invalid_severity(self):
        """Test error event validation with invalid severity."""
        with pytest.raises(ValueError, match="Severity must be one of"):
            JoyrideErrorEvent(
                event_type="error.test",
                source="test.source",
                error_type="TestError",
                error_message="Test error",
                severity="invalid",
            )


class TestHealthEvent:
    """Test JoyrideHealthEvent class."""

    def test_health_event_creation_minimal(self):
        """Test creating health event with minimal parameters."""
        event = JoyrideHealthEvent(
            event_type="health.check.passed",
            source="health.monitor",
            component="dns.server",
            health_status="healthy",
            check_name="dns_query_test",
            check_result=True,
        )

        assert event.event_type == "health.check.passed"
        assert event.source == "health.monitor"
        assert event.component == "dns.server"
        assert event.health_status == "healthy"
        assert event.check_name == "dns_query_test"
        assert event.check_result is True
        assert event.check_message is None
        assert event.check_duration is None
        assert event.metrics == {}

    def test_health_event_creation_full(self):
        """Test creating health event with all parameters."""
        metrics = {"response_time": 0.05, "queries_per_second": 150}

        event = JoyrideHealthEvent(
            event_type="health.check.failed",
            source="health.monitor",
            component="docker.monitor",
            health_status="unhealthy",
            check_name="docker_api_check",
            check_result=False,
            check_message="Docker API unreachable",
            check_duration=5.0,
            metrics=metrics,
            data={"error_count": 3},
        )

        assert event.component == "docker.monitor"
        assert event.health_status == "unhealthy"
        assert event.check_name == "docker_api_check"
        assert event.check_result is False
        assert event.check_message == "Docker API unreachable"
        assert event.check_duration == 5.0
        assert event.metrics == metrics
        assert event.data["error_count"] == 3

    def test_health_event_properties(self):
        """Test health event property access."""
        event = JoyrideHealthEvent(
            event_type="health.status.degraded",
            source="health.aggregator",
            component="swim.cluster",
            health_status="degraded",
            check_name="cluster_connectivity",
            check_result=False,
            check_duration=2.5,
        )

        # Test property access
        assert event.component == "swim.cluster"
        assert event.health_status == "degraded"
        assert event.check_name == "cluster_connectivity"
        assert event.check_result is False
        assert event.check_duration == 2.5

        # Test that properties come from data
        assert event.data["component"] == "swim.cluster"
        assert event.data["health_status"] == "degraded"
        assert event.data["check_name"] == "cluster_connectivity"
        assert event.data["check_result"] is False
        assert event.data["check_duration"] == 2.5


class TestEventTypeInheritance:
    """Test that all event types properly inherit from JoyrideEvent base class."""

    def test_all_events_inherit_from_event(self):
        """Test that all event types are instances of JoyrideEvent."""
        from app.events import JoyrideEvent

        # Create instances of all event types
        dns_event = JoyrideDNSEvent("test", "test", "test.com")
        container_event = JoyrideContainerEvent("test", "test", "123", "test", "nginx")
        node_event = JoyrideNodeEvent("test", "test", "node1", "1.1.1.1", 7946, "alive")
        file_event = JoyrideFileEvent("test", "test", "/test", "modified")
        system_event = JoyrideSystemEvent("test", "test", "comp", "start", "success")
        error_event = JoyrideErrorEvent("test", "test", "Error", "Test error")
        health_event = JoyrideHealthEvent(
            "test", "test", "comp", "healthy", "test", True
        )

        # Verify inheritance
        assert isinstance(dns_event, JoyrideEvent)
        assert isinstance(container_event, JoyrideEvent)
        assert isinstance(node_event, JoyrideEvent)
        assert isinstance(file_event, JoyrideEvent)
        assert isinstance(system_event, JoyrideEvent)
        assert isinstance(error_event, JoyrideEvent)
        assert isinstance(health_event, JoyrideEvent)

    def test_all_events_have_base_properties(self):
        """Test that all event types have base JoyrideEvent properties."""
        events = [
            JoyrideDNSEvent("dns.test", "test", "test.com"),
            JoyrideContainerEvent("container.test", "test", "123", "test", "nginx"),
            JoyrideNodeEvent("node.test", "test", "node1", "1.1.1.1", 7946, "alive"),
            JoyrideFileEvent("file.test", "test", "/test", "modified"),
            JoyrideSystemEvent("system.test", "test", "comp", "start", "success"),
            JoyrideErrorEvent("error.test", "test", "Error", "Test error"),
            JoyrideHealthEvent("health.test", "test", "comp", "healthy", "test", True),
        ]

        for event in events:
            # All events should have these base properties
            assert hasattr(event, "event_id")
            assert hasattr(event, "event_type")
            assert hasattr(event, "source")
            assert hasattr(event, "timestamp")
            assert hasattr(event, "data")
            assert hasattr(event, "metadata")

            # Verify they're accessible
            assert event.event_id is not None
            assert event.event_type is not None
            assert event.source is not None
            assert event.timestamp is not None
            assert event.data is not None
            assert event.metadata is not None

    def test_all_events_have_to_dict_method(self):
        """Test that all event types have to_dict method."""
        events = [
            JoyrideDNSEvent("dns.test", "test", "test.com"),
            JoyrideContainerEvent("container.test", "test", "123", "test", "nginx"),
            JoyrideNodeEvent("node.test", "test", "node1", "1.1.1.1", 7946, "alive"),
            JoyrideFileEvent("file.test", "test", "/test", "modified"),
            JoyrideSystemEvent("system.test", "test", "comp", "start", "success"),
            JoyrideErrorEvent("error.test", "test", "Error", "Test error"),
            JoyrideHealthEvent("health.test", "test", "comp", "healthy", "test", True),
        ]

        for event in events:
            event_dict = event.to_dict()
            assert isinstance(event_dict, dict)
            assert "event_id" in event_dict
            assert "event_type" in event_dict
            assert "source" in event_dict
            assert "timestamp" in event_dict
            assert "data" in event_dict
            assert "metadata" in event_dict
