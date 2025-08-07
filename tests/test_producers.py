"""Tests for Event Producers."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.joyride.events import EventBus


class TestEventProducer:
    """Test EventProducer base class."""

    @pytest.fixture
    def event_bus(self):
        """Create mock event bus."""
        return AsyncMock(spec=EventBus)

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return {"test_key": "test_value"}

    def test_event_producer_creation(self, event_bus, config):
        """Test EventProducer creation."""
        from app.producers.event_producer import EventProducer

        # Note: EventProducer is abstract, so we test with a concrete implementation
        producer = None  # Would need concrete implementation

        # This test validates the structure exists
        assert EventProducer is not None

    @pytest.mark.asyncio
    async def test_producer_lifecycle(self, event_bus, config):
        """Test producer lifecycle methods."""
        # This would test start/stop methods when concrete implementation exists
        pass


class TestDockerEventProducer:
    """Test Docker event producer."""

    @pytest.fixture
    def event_bus(self):
        """Create mock event bus."""
        return AsyncMock(spec=EventBus)

    @pytest.fixture
    def config(self):
        """Create Docker producer configuration."""
        return {
            "docker_url": "unix://var/run/docker.sock",
            "api_version": "auto",
            "timeout": 60,
        }

    def test_docker_producer_creation(self, event_bus, config):
        """Test Docker producer creation."""
        from app.producers.docker_producer import DockerEventProducer

        producer = DockerEventProducer(event_bus, "test_docker", config)
        assert producer._docker_url == "unix://var/run/docker.sock"
        assert producer._api_version == "auto"
        assert producer._timeout == 60

    def test_docker_event_types(self):
        """Test Docker event type definitions."""
        from app.producers.docker_events import DockerEventType

        # Test key event types exist
        assert DockerEventType.CONTAINER_START == "container.start"
        assert DockerEventType.CONTAINER_STOP == "container.stop"
        assert DockerEventType.NETWORK_CREATE == "network.create"

    def test_docker_container_event(self):
        """Test Docker container event creation."""
        from datetime import datetime, timezone

        from app.producers.docker_events import DockerContainerEvent, DockerEventType

        event = DockerContainerEvent(
            docker_event_type=DockerEventType.CONTAINER_START,
            source="test",
            docker_event_id="test123",
            docker_timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            docker_action="start",
            actor_id="container123",
            actor_type="container",
            container_id="container123",
            container_name="test_container",
            container_image="nginx:latest",
            target_node_address="192.168.1.100",
            target_node_port=80,
        )

        assert event.container_id == "container123"
        assert event.short_container_id == "container123"
        assert event.is_container_event is True


class TestSWIMEventProducer:
    """Test SWIM event producer."""

    @pytest.fixture
    def event_bus(self):
        """Create mock event bus."""
        return AsyncMock(spec=EventBus)

    @pytest.fixture
    def config(self):
        """Create SWIM producer configuration."""
        return {
            "node_id": "test_node_001",
            "cluster_id": "test_cluster",
            "protocol_version": "1.0",
            "monitoring_interval": 10,
        }

    def test_swim_producer_creation(self, event_bus, config):
        """Test SWIM producer creation."""
        from app.producers.swim_producer import SWIMEventProducer

        producer = SWIMEventProducer(event_bus, "test_swim", config)
        assert producer._node_id == "test_node_001"
        assert producer._cluster_id == "test_cluster"
        assert producer._monitoring_interval == 10

    def test_swim_event_types(self):
        """Test SWIM event type definitions."""
        from app.producers.swim_events import SWIMEventType

        # Test key event types exist
        assert SWIMEventType.NODE_JOIN == "swim.node.join"
        assert SWIMEventType.NODE_FAILED == "swim.node.failed"
        assert SWIMEventType.MEMBERSHIP_UPDATE == "swim.membership.update"

    def test_swim_node_event(self):
        """Test SWIM node event creation."""
        from app.producers.swim_events import (
            SWIMEventType,
            SWIMNodeEvent,
            SWIMNodeState,
        )

        event = SWIMNodeEvent(
            swim_event_type=SWIMEventType.NODE_JOIN,
            node_id="test_node_001",
            source="test",
            target_node_id="new_node_002",
            target_node_address="192.168.1.101",
            target_node_port=7946,
            target_node_state=SWIMNodeState.ALIVE,
        )

        assert event.target_node_id == "new_node_002"
        assert event.is_alive is True
        assert event.is_failed is False


class TestHostsFileEventProducer:
    """Test hosts file event producer."""

    @pytest.fixture
    def event_bus(self):
        """Create mock event bus."""
        return AsyncMock(spec=EventBus)

    @pytest.fixture
    def config(self):
        """Create hosts file producer configuration."""
        return {
            "hosts_file_paths": ["/etc/hosts"],
            "polling_interval": 5,
            "create_backups": True,
            "max_backups": 5,
        }

    def test_hosts_producer_creation(self, event_bus, config):
        """Test hosts file producer creation."""
        from app.producers.hosts_producer import HostsFileEventProducer

        producer = HostsFileEventProducer(event_bus, "test_hosts", config)
        assert producer._hosts_file_paths == ["/etc/hosts"]
        assert producer._polling_interval == 5
        assert producer._create_backups is True

    def test_hosts_event_types(self):
        """Test hosts file event type definitions."""
        from app.producers.hosts_events import HostsFileEventType

        # Test key event types exist
        assert HostsFileEventType.FILE_MODIFIED == "hosts.file.modified"
        assert HostsFileEventType.ENTRY_ADDED == "hosts.entry.added"
        assert HostsFileEventType.PARSE_ERROR == "hosts.parse.error"

    def test_hosts_entry_event(self):
        """Test hosts entry event creation."""
        from app.producers.hosts_events import HostsEntryEvent, HostsFileEventType

        event = HostsEntryEvent(
            hosts_event_type=HostsFileEventType.ENTRY_ADDED,
            source="test",
            file_path="/etc/hosts",
            ip_address="192.168.1.100",
            hostnames=["test.local", "test"],
            line_number=10,
        )

        assert event.ip_address == "192.168.1.100"
        assert event.primary_hostname == "test.local"
        assert event.is_localhost is False


class TestSystemEventProducer:
    """Test system event producer."""

    @pytest.fixture
    def event_bus(self):
        """Create mock event bus."""
        return AsyncMock(spec=EventBus)

    @pytest.fixture
    def config(self):
        """Create system producer configuration."""
        return {
            "monitoring_interval": 30,
            "cpu_threshold": 80,
            "memory_threshold": 80,
            "disk_threshold": 85,
        }

    def test_system_producer_creation(self, event_bus, config):
        """Test system producer creation."""
        from app.producers.system_producer import SystemEventProducer

        producer = SystemEventProducer(event_bus, "test_system", config)
        assert producer._monitoring_interval == 30
        assert producer._cpu_threshold == 80
        assert producer._memory_threshold == 80

    def test_system_event_types(self):
        """Test system event type definitions."""
        from app.producers.system_events import SystemEventType

        # Test key event types exist
        assert SystemEventType.SYSTEM_STARTUP == "system.startup"
        assert SystemEventType.MEMORY_PRESSURE == "system.memory.pressure"
        assert SystemEventType.CPU_HIGH_USAGE == "system.cpu.high_usage"

    def test_system_resource_event(self):
        """Test system resource event creation."""
        from app.producers.system_events import SystemEventType, SystemResourceEvent

        event = SystemResourceEvent(
            system_event_type=SystemEventType.CPU_HIGH_USAGE,
            source="test",
            hostname="test-host",
            resource_type="cpu",
            current_value=85.0,
            threshold_value=80.0,
            unit="percent",
        )

        assert event.resource_type == "cpu"
        assert event.current_value == 85.0
        assert event.is_critical is False
        assert event.is_warning is True


@pytest.mark.asyncio
async def test_event_producer_integration():
    """Test event producer integration."""
    # This test would verify that producers can actually publish events
    # when integrated with the event bus system
    
    event_bus = AsyncMock(spec=EventBus)
    
    # Test that we can import all producers
    from app.producers import (
        DockerEventProducer,
        EventProducer,
        HostsFileEventProducer,
        SWIMEventProducer,
        SystemEventProducer,
    )

    # Verify all classes are available
    assert EventProducer is not None
    assert DockerEventProducer is not None
    assert SWIMEventProducer is not None
    assert HostsFileEventProducer is not None
    assert SystemEventProducer is not None


def test_producer_module_exports():
    """Test that producer module exports all expected classes."""
    from app.producers import __all__
    
    expected_exports = [
        "EventProducer",
        "DockerEventProducer",
        "SWIMEventProducer", 
        "HostsFileEventProducer",
        "SystemEventProducer",
    ]
    
    for export in expected_exports:
        assert export in __all__
