"""Tests for Event Producers."""

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from app.joyride.events import Event, EventBus


class ConcreteEventProducer:
    """Concrete implementation of EventProducer for testing."""

    def __init__(self, event_bus, producer_name, config=None):
        from app.producers.event_producer import EventProducer

        class TestProducer(EventProducer):
            async def _start_producer(self):
                self._register_event_type("test.event")

            async def _stop_producer(self):
                pass

            async def _run_producer(self):
                while self._is_running:
                    await asyncio.sleep(0.1)

        self.producer = TestProducer(event_bus, producer_name, config)

    def __getattr__(self, name):
        return getattr(self.producer, name)

    def __setattr__(self, name, value):
        if name == "producer":
            super().__setattr__(name, value)
        else:
            setattr(self.producer, name, value)


class TestEventProducer:
    """Test EventProducer base class."""

    @pytest.fixture
    def event_bus(self):
        """Create mock event bus."""
        return AsyncMock(spec=EventBus)

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return {"test_key": "test_value", "monitoring_interval": 5}

    @pytest.fixture
    def producer(self, event_bus, config):
        """Create concrete producer for testing."""
        return ConcreteEventProducer(event_bus, "test_producer", config)

    def test_event_producer_creation(self, event_bus, config):
        """Test EventProducer creation."""
        producer = ConcreteEventProducer(event_bus, "test", config)
        assert producer.producer_name == "test"
        assert producer.event_count == 0
        assert producer.error_count == 0
        assert producer.last_event_time is None
        assert not producer.is_running
        assert producer._config == config

    def test_producer_properties(self, producer):
        """Test producer property accessors."""
        assert producer.producer_name == "test_producer"
        assert producer.event_count == 0
        assert producer.error_count == 0
        assert producer.last_event_time is None
        assert isinstance(producer.supported_event_types, set)
        assert not producer.is_running

    @pytest.mark.asyncio
    async def test_producer_lifecycle_start_stop(self, producer):
        """Test producer start and stop lifecycle."""
        assert not producer.is_running

        # Start producer
        await producer.start()
        assert producer.is_running
        assert "test.event" in producer.supported_event_types

        # Stop producer
        await producer.stop()
        assert not producer.is_running

    @pytest.mark.asyncio
    async def test_producer_start_already_running(self, producer):
        """Test starting producer when already running."""
        await producer.start()

        # Starting again should not raise error
        await producer.start()
        assert producer.is_running

    @pytest.mark.asyncio
    async def test_producer_stop_not_running(self, producer):
        """Test stopping producer when not running."""
        assert not producer.is_running

        # Stopping when not running should not raise error
        await producer.stop()
        assert not producer.is_running

    @pytest.mark.asyncio
    async def test_producer_start_failure(self, event_bus, config):
        """Test producer start failure handling."""
        from app.producers.event_producer import EventProducer

        class FailingProducer(EventProducer):
            async def _start_producer(self):
                raise Exception("Start failed")

            async def _stop_producer(self):
                pass

        producer = FailingProducer(event_bus, "failing", config)

        with pytest.raises(Exception, match="Start failed"):
            await producer.start()

        assert not producer.is_running

    @pytest.mark.asyncio
    async def test_producer_stop_failure(self, event_bus, config):
        """Test producer stop failure handling."""
        from app.producers.event_producer import EventProducer

        class FailingStopProducer(EventProducer):
            async def _start_producer(self):
                pass

            async def _stop_producer(self):
                raise Exception("Stop failed")

        producer = FailingStopProducer(event_bus, "failing_stop", config)
        await producer.start()

        with pytest.raises(Exception, match="Stop failed"):
            await producer.stop()

    def test_publish_event_success(self, producer):
        """Test successful event publishing."""
        # Mock event
        event = Mock(spec=Event)
        event.event_type = "test.event"
        event.source = "test"
        event.metadata = {}

        # Start producer first
        producer._is_running = True

        # Publish event
        producer.publish_event(event)

        assert producer.event_count == 1
        assert producer.last_event_time is not None
        assert producer.error_count == 0
        producer._event_bus.publish.assert_called_once_with(event)

    def test_publish_event_not_running(self, producer):
        """Test publishing event when producer not running."""
        event = Mock(spec=Event)
        event.event_type = "test.event"

        with pytest.raises(RuntimeError, match="Producer test_producer is not running"):
            producer.publish_event(event)

    def test_publish_event_error(self, producer):
        """Test event publishing with error."""
        event = Mock(spec=Event)
        event.event_type = "test.event"
        event.source = "test"
        event.metadata = {}

        producer._is_running = True
        producer._event_bus.publish.side_effect = Exception("Publish failed")

        with pytest.raises(Exception, match="Publish failed"):
            producer.publish_event(event)

        assert producer.error_count == 1

    def test_get_metrics(self, producer):
        """Test getting producer metrics."""
        producer._event_count = 5
        producer._error_count = 1
        producer._last_event_time = datetime(2024, 1, 1, 12, 0, 0)
        producer._is_running = True
        producer._register_event_type("test.event")

        metrics = producer.get_metrics()

        assert metrics["producer_name"] == "test_producer"
        assert metrics["is_running"] is True
        assert metrics["event_count"] == 5
        assert metrics["error_count"] == 1
        assert metrics["last_event_time"] == "2024-01-01T12:00:00"
        assert "test.event" in metrics["supported_event_types"]
        assert metrics["config"] == producer._config

    def test_get_config_value(self, producer):
        """Test getting configuration values."""
        assert producer._get_config_value("test_key") == "test_value"
        assert producer._get_config_value("missing_key", "default") == "default"
        assert producer._get_config_value("missing_key") is None

    def test_register_event_type(self, producer):
        """Test registering event types."""
        producer._register_event_type("new.event")
        assert "new.event" in producer.supported_event_types

    @pytest.mark.asyncio
    async def test_health_check_not_running(self, producer):
        """Test health check when not running."""
        assert not await producer.health_check()

    @pytest.mark.asyncio
    async def test_health_check_high_error_rate(self, producer):
        """Test health check with high error rate."""
        producer._is_running = True
        producer._event_count = 10
        producer._error_count = 6  # 60% error rate

        assert not await producer.health_check()

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, producer):
        """Test health check when healthy."""
        producer._is_running = True
        producer._event_count = 10
        producer._error_count = 2  # 20% error rate

        assert await producer.health_check()

    @pytest.mark.asyncio
    async def test_health_check_no_events(self, producer):
        """Test health check with no events."""
        producer._is_running = True
        producer._event_count = 0
        producer._error_count = 0

        assert await producer.health_check()

    @pytest.mark.asyncio
    async def test_health_check_exception(self, producer):
        """Test health check with exception."""
        producer._is_running = True

        # Mock the producer health check to raise exception
        with patch.object(
            producer.producer,
            "_producer_health_check",
            side_effect=Exception("Health check failed"),
        ):
            assert not await producer.health_check()

    @pytest.mark.asyncio
    async def test_producer_health_check_default(self, producer):
        """Test default producer health check."""
        assert await producer._producer_health_check()

    @pytest.mark.asyncio
    async def test_producer_task_management(self, producer):
        """Test producer async task management."""
        await producer.start()

        # Verify task was created
        assert producer._task is not None
        assert not producer._task.done()

        await producer.stop()

        # Verify task was cancelled
        assert producer._task.done()
        assert producer._task.cancelled()


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
            "event_filters": {"type": ["container"]},
        }

    @pytest.fixture
    def docker_producer(self, event_bus, config):
        """Create Docker producer instance."""
        from app.producers.docker_producer import DockerEventProducer

        return DockerEventProducer(event_bus, "test_docker", config)

    def test_docker_producer_creation(self, event_bus, config):
        """Test Docker producer creation."""
        from app.producers.docker_producer import DockerEventProducer

        producer = DockerEventProducer(event_bus, "test_docker", config)
        assert producer._docker_url == "unix://var/run/docker.sock"
        assert producer._api_version == "auto"
        assert producer._timeout == 60
        assert producer._event_filters == {"type": ["container"]}
        assert producer._docker_client is None

    def test_docker_producer_default_config(self, event_bus):
        """Test Docker producer with default configuration."""
        from app.producers.docker_producer import DockerEventProducer

        producer = DockerEventProducer(event_bus, "test_docker", {})
        assert producer._docker_url == "unix://var/run/docker.sock"
        assert producer._api_version == "auto"
        assert producer._timeout == 60
        assert producer._event_filters == {}

    def test_docker_producer_map_docker_event_type(self, docker_producer):
        """Test mapping Docker event types."""
        from app.producers.docker_events import DockerEventType

        # Test container events
        assert (
            docker_producer._map_docker_event_type("container", "start")
            == DockerEventType.CONTAINER_START
        )
        assert (
            docker_producer._map_docker_event_type("container", "stop")
            == DockerEventType.CONTAINER_STOP
        )

        # Test network events
        assert (
            docker_producer._map_docker_event_type("network", "create")
            == DockerEventType.NETWORK_CREATE
        )

        # Test unknown events
        assert docker_producer._map_docker_event_type("unknown", "action") is None

    @pytest.mark.asyncio
    async def test_docker_producer_create_container_event(self, docker_producer):
        """Test creating container events."""
        from app.producers.docker_events import DockerEventType

        common_fields = {
            "source": "test_docker",
            "docker_event_id": "event123",
            "docker_event_type": DockerEventType.CONTAINER_START,
            "docker_timestamp": datetime.fromtimestamp(1704067200),
            "docker_action": "start",
            "actor_id": "container123",
            "actor_type": "container",
            "actor_attributes": {"name": "test_container", "image": "nginx:latest"},
            "scope": "local",
            "time_nano": 1704067200000000000,
        }

        event_data = {}

        event = await docker_producer._create_container_event(common_fields, event_data)

        assert event is not None
        assert event.container_id == "container123"
        assert event.container_name == "test_container"
        assert event.container_image == "nginx:latest"

    @pytest.mark.asyncio
    async def test_docker_producer_create_network_event(self, docker_producer):
        """Test creating network events."""
        from app.producers.docker_events import DockerEventType

        common_fields = {
            "source": "test_docker",
            "docker_event_id": "event123",
            "docker_event_type": DockerEventType.NETWORK_CREATE,
            "docker_timestamp": 1704067200,
            "docker_action": "create",
            "actor_id": "network123",
            "actor_type": "network",
            "actor_attributes": {"name": "test_network", "driver": "bridge"},
            "scope": "local",
            "time_nano": 1704067200000000000,
        }

        event_data = {}

        event = await docker_producer._create_network_event(common_fields, event_data)

        assert event is not None
        assert event.network_id == "network123"
        assert event.network_name == "test_network"
        assert event.network_driver == "bridge"

    @pytest.mark.asyncio
    async def test_docker_producer_create_volume_event(self, docker_producer):
        """Test creating volume events."""
        from app.producers.docker_events import DockerEventType

        common_fields = {
            "source": "test_docker",
            "docker_event_id": "event123",
            "docker_event_type": DockerEventType.VOLUME_CREATE,
            "docker_timestamp": 1704067200,
            "docker_action": "create",
            "actor_id": "volume123",
            "actor_type": "volume",
            "actor_attributes": {
                "driver": "local",
                "mountpoint": "/var/lib/docker/volumes/volume123",
            },
            "scope": "local",
            "time_nano": 1704067200000000000,
        }

        event_data = {}

        event = await docker_producer._create_volume_event(common_fields, event_data)

        assert event is not None
        assert event.volume_name == "volume123"
        assert event.volume_driver == "local"

    @pytest.mark.asyncio
    async def test_docker_producer_create_image_event(self, docker_producer):
        """Test creating image events."""
        from app.producers.docker_events import DockerEventType

        common_fields = {
            "source": "test_docker",
            "docker_event_id": "event123",
            "docker_event_type": DockerEventType.IMAGE_PULL,
            "docker_timestamp": 1704067200,
            "docker_action": "pull",
            "actor_id": "image123",
            "actor_type": "image",
            "actor_attributes": {"name": "nginx:latest", "repository": "nginx"},
            "scope": "local",
            "time_nano": 1704067200000000000,
        }

        event_data = {}

        event = await docker_producer._create_image_event(common_fields, event_data)

        assert event is not None
        assert event.image_id == "image123"
        assert event.image_name == "nginx"
        assert event.image_tags == ["latest"]

    @pytest.mark.asyncio
    async def test_docker_producer_start_success(self, docker_producer):
        """Test successful Docker producer start."""
        with patch("docker.DockerClient") as mock_client_class:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_client_class.return_value = mock_client

            await docker_producer.start()

            assert docker_producer.is_running
            assert docker_producer._docker_client is not None
            mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_docker_producer_start_connection_failure(self, docker_producer):
        """Test Docker producer start with connection failure."""
        with patch("docker.DockerClient") as mock_client_class:
            mock_client_class.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                await docker_producer.start()

            assert not docker_producer.is_running

    @pytest.mark.asyncio
    async def test_docker_producer_stop(self, docker_producer):
        """Test Docker producer stop."""
        # Mock successful start
        with patch("docker.DockerClient") as mock_client_class:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_client_class.return_value = mock_client

            await docker_producer.start()
            assert docker_producer.is_running

            await docker_producer.stop()
            assert not docker_producer.is_running


class TestSWIMEventProducer:
    """Test SWIM event producer."""

    @pytest.fixture
    def event_bus(self):
        """Create mock event bus."""
        return AsyncMock(spec=EventBus)
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
            "backup_directory": "/tmp/test_hosts_backups",
            "max_backups": 5,
            "parse_entries": True,
        }

    @pytest.fixture
    def hosts_producer(self, event_bus, config):
        """Create hosts producer instance."""
        from app.producers.hosts_producer import HostsFileEventProducer

        return HostsFileEventProducer(event_bus, "test_hosts", config)

    def test_hosts_producer_creation(self, event_bus, config):
        """Test hosts file producer creation."""
        from app.producers.hosts_producer import HostsFileEventProducer

        producer = HostsFileEventProducer(event_bus, "test_hosts", config)
        assert producer._hosts_file_paths == ["/etc/hosts"]
        assert producer._polling_interval == 5
        assert producer._create_backups is True
        assert producer._max_backups == 5
        assert producer._parse_entries is True

    def test_hosts_producer_default_config(self, event_bus):
        """Test hosts producer with default configuration."""
        from app.producers.hosts_producer import HostsFileEventProducer

        producer = HostsFileEventProducer(event_bus, "test_hosts", {})
        assert producer._hosts_file_paths == ["/etc/hosts"]
        assert producer._polling_interval == 5
        assert producer._create_backups is True
        assert producer._max_backups == 10
        assert producer._parse_entries is True

    @pytest.mark.asyncio
    async def test_hosts_producer_start(self, hosts_producer):
        """Test hosts producer start."""
        with patch("pathlib.Path.mkdir") as mock_mkdir, patch.object(
            hosts_producer, "_initialize_file_states"
        ) as mock_init:
            await hosts_producer.start()

            assert hosts_producer.is_running
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_hosts_producer_stop(self, hosts_producer):
        """Test hosts producer stop."""
        hosts_producer._file_watchers = {"test": "watcher"}

        await hosts_producer.stop()

        assert not hosts_producer.is_running
        assert hosts_producer._file_watchers == {}

    def test_hosts_producer_calculate_file_checksum(self, hosts_producer):
        """Test calculating file checksum."""
        test_content = "127.0.0.1 localhost\n"

        with patch("builtins.open", mock_open(read_data=test_content.encode())):
            checksum = hosts_producer._calculate_file_checksum("/test/hosts")

            expected = hashlib.md5(test_content.encode()).hexdigest()
            assert checksum == expected

    def test_hosts_producer_calculate_file_checksum_error(self, hosts_producer):
        """Test calculating file checksum with error."""
        with patch("builtins.open", side_effect=IOError("File not found")):
            checksum = hosts_producer._calculate_file_checksum("/nonexistent/hosts")
            assert checksum is None

    def test_hosts_producer_parse_hosts_line_valid(self, hosts_producer):
        """Test parsing valid hosts file line."""
        line = "192.168.1.100 example.com www.example.com"

        result = hosts_producer._parse_hosts_line(line, 1)

        assert result is not None
        assert result["ip_address"] == "192.168.1.100"
        assert result["hostnames"] == ["example.com", "www.example.com"]
        assert result["primary_hostname"] == "example.com"
        assert result["line_number"] == 1

    def test_hosts_producer_parse_hosts_line_comment(self, hosts_producer):
        """Test parsing comment line."""
        line = "# This is a comment"

        result = hosts_producer._parse_hosts_line(line, 1)
        assert result is None

    def test_hosts_producer_parse_hosts_line_empty(self, hosts_producer):
        """Test parsing empty line."""
        line = "   "

        result = hosts_producer._parse_hosts_line(line, 1)
        assert result is None

    def test_hosts_producer_parse_hosts_line_invalid(self, hosts_producer):
        """Test parsing invalid line."""
        line = "invalid line without ip"

        result = hosts_producer._parse_hosts_line(line, 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_hosts_producer_create_backup(self, hosts_producer):
        """Test creating backup file."""
        original_content = "127.0.0.1 localhost"

        with patch("builtins.open", mock_open(read_data=original_content)), patch(
            "pathlib.Path.exists", return_value=True
        ), patch("pathlib.Path.write_text") as mock_write, patch(
            "pathlib.Path.stat"
        ) as mock_stat:
            mock_stat.return_value = Mock(st_size=len(original_content))
            hosts_producer._is_running = True  # Need this for publish_event

            backup_path = await hosts_producer._create_backup("/etc/hosts")

            assert backup_path is not None
            assert "/tmp/test_hosts_backups" in str(backup_path)
            mock_write.assert_called_once_with(original_content)

    @pytest.mark.asyncio
    async def test_hosts_producer_create_backup_error(self, hosts_producer):
        """Test creating backup with error."""
        with patch("builtins.open", side_effect=IOError("Read error")):
            backup_path = await hosts_producer._create_backup("/etc/hosts")
            assert backup_path is None

    @pytest.mark.asyncio
    async def test_hosts_producer_cleanup_old_backups(self, hosts_producer):
        """Test cleaning up old backups."""
        # Mock multiple backup files
        mock_files = [
            Mock(stat=Mock(return_value=Mock(st_mtime=1000)), unlink=Mock()),
            Mock(stat=Mock(return_value=Mock(st_mtime=2000)), unlink=Mock()),
            Mock(stat=Mock(return_value=Mock(st_mtime=3000)), unlink=Mock()),
            Mock(stat=Mock(return_value=Mock(st_mtime=4000)), unlink=Mock()),
            Mock(stat=Mock(return_value=Mock(st_mtime=5000)), unlink=Mock()),
            Mock(stat=Mock(return_value=Mock(st_mtime=6000)), unlink=Mock()),
        ]

        hosts_producer._max_backups = 3

        # Mock the backup directory and its methods
        with patch.object(hosts_producer, "_backup_directory") as mock_backup_dir:
            mock_backup_dir.exists.return_value = True
            mock_backup_dir.glob.return_value = mock_files

            await hosts_producer._cleanup_old_backups()

            # Should delete the 3 oldest files
            mock_files[0].unlink.assert_called_once()
            mock_files[1].unlink.assert_called_once()
            mock_files[2].unlink.assert_called_once()
            mock_files[3].unlink.assert_not_called()

    @pytest.mark.asyncio
    async def test_hosts_producer_check_hosts_file_no_change(self, hosts_producer):
        """Test checking hosts file with no changes."""
        file_path = "/etc/hosts"
        test_checksum = "abc123"

        hosts_producer._last_checksums[file_path] = test_checksum

        with patch.object(
            hosts_producer, "_calculate_file_checksum", return_value=test_checksum
        ):
            await hosts_producer._check_hosts_file(file_path)

            # Should not publish any events for unchanged file

    @pytest.mark.asyncio
    async def test_hosts_producer_check_hosts_file_changed(self, hosts_producer):
        """Test checking hosts file with changes."""
        file_path = "/etc/hosts"
        old_checksum = "abc123"
        new_checksum = "def456"

        hosts_producer._last_checksums[file_path] = old_checksum

        with patch.object(
            hosts_producer, "_calculate_file_checksum", return_value=new_checksum
        ), patch.object(hosts_producer, "_process_hosts_file_change") as mock_process:
            await hosts_producer._check_hosts_file(file_path)

            mock_process.assert_called_once_with(file_path, old_checksum, new_checksum)
            assert hosts_producer._last_checksums[file_path] == new_checksum

    @pytest.mark.asyncio
    async def test_hosts_producer_check_hosts_file_error(self, hosts_producer):
        """Test checking hosts file with error."""
        file_path = "/etc/hosts"

        with patch.object(
            hosts_producer, "_calculate_file_checksum", return_value=None
        ):
            await hosts_producer._check_hosts_file(file_path)

            # Should handle error gracefully

    @pytest.mark.asyncio
    async def test_hosts_producer_process_hosts_file_change(self, hosts_producer):
        """Test processing hosts file changes."""
        file_path = "/etc/hosts"
        old_checksum = "abc123"
        new_checksum = "def456"

        with patch.object(
            hosts_producer, "_create_backup", return_value=Path("/backup/file")
        ) as mock_backup, patch.object(
            hosts_producer, "_parse_hosts_file"
        ) as mock_parse, patch.object(
            hosts_producer, "publish_event"
        ) as mock_publish:
            hosts_producer._is_running = True
            await hosts_producer._process_hosts_file_change(
                file_path, old_checksum, new_checksum
            )

            mock_backup.assert_called_once_with(file_path)
            mock_parse.assert_called_once_with(file_path)
            assert mock_publish.call_count >= 1  # Should publish modification event

    @pytest.mark.asyncio
    async def test_hosts_producer_parse_hosts_file(self, hosts_producer):
        """Test parsing entire hosts file."""
        file_content = """# This is a comment
127.0.0.1 localhost
192.168.1.100 example.com www.example.com
# Another comment
invalid line
"""
        file_path = "/etc/hosts"

        with patch("builtins.open", mock_open(read_data=file_content)), patch.object(
            hosts_producer, "publish_event"
        ) as mock_publish:
            hosts_producer._is_running = True
            await hosts_producer._parse_hosts_file(file_path)

            # Should publish events for valid entries
            assert mock_publish.call_count >= 2  # At least 2 valid entries

    @pytest.mark.asyncio
    async def test_hosts_producer_initialize_file_states(self, hosts_producer):
        """Test initializing file states."""
        hosts_producer._hosts_file_paths = ["/etc/hosts", "/tmp/hosts"]

        with patch("os.path.exists", return_value=True), patch(
            "os.stat"
        ) as mock_stat, patch.object(
            hosts_producer, "_calculate_file_checksum", side_effect=["abc123", "def456"]
        ):
            # Mock stat results
            mock_stat.return_value = Mock(
                st_size=1000, st_mtime=1234567890, st_mode=0o644
            )

            await hosts_producer._initialize_file_states()

            assert hosts_producer._last_checksums["/etc/hosts"] == "abc123"
            assert hosts_producer._last_checksums["/tmp/hosts"] == "def456"

    @pytest.mark.asyncio
    async def test_hosts_producer_health_check(self, hosts_producer):
        """Test hosts producer health check."""
        hosts_producer._is_running = True

        # Mock file existence checks
        with patch("pathlib.Path.exists", return_value=True):
            result = await hosts_producer._producer_health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_hosts_producer_health_check_missing_file(self, hosts_producer):
        """Test health check with missing monitored file."""
        hosts_producer._is_running = True

        # Mock file doesn't exist
        with patch("pathlib.Path.exists", return_value=False):
            result = await hosts_producer._producer_health_check()
            assert result is False

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
