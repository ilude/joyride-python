import time
from threading import Event
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from app.docker_monitor import DockerEventMonitor


class TestDockerEventMonitor:
    """Test Docker event monitoring functionality."""

    @pytest.fixture
    def dns_callback(self):
        """Mock DNS callback function."""
        return Mock()

    @pytest.fixture
    def monitor(self, dns_callback):
        """Create DockerEventMonitor instance."""
        return DockerEventMonitor(dns_callback)

    @pytest.fixture
    def mock_container_with_label(self):
        """Mock container with joyride.host.name label."""
        container = Mock()
        container.attrs = {
            "Config": {
                "Labels": {
                    "joyride.host.name": "test.example.com"
                }
            },
            "NetworkSettings": {
                "Networks": {
                    "bridge": {
                        "IPAddress": "172.17.0.2"
                    }
                }
            }
        }
        return container

    @pytest.fixture
    def mock_container_without_label(self):
        """Mock container without joyride.host.name label."""
        container = Mock()
        container.attrs = {
            "Config": {
                "Labels": {}
            },
            "NetworkSettings": {
                "Networks": {
                    "bridge": {
                        "IPAddress": "172.17.0.3"
                    }
                }
            }
        }
        return container

    def test_handle_container_start_with_label(
        self, monitor, dns_callback, mock_container_with_label
    ):
        """Test container start event with joyride.host.name label."""
        with patch.object(monitor, "client") as mock_client:
            mock_client.containers.get.return_value = mock_container_with_label

            monitor._handle_container_start("container123")

            mock_client.containers.get.assert_called_once_with("container123")
            # DNS callback is called with container IP, but main.py will override with HOST_IP
            dns_callback.assert_called_once_with(
                "add", "test.example.com", "172.17.0.2"
            )

    def test_handle_container_start_without_label(self, monitor, dns_callback, mock_container_without_label):
        """Test container start event without joyride.host.name label."""
        with patch.object(monitor, 'client') as mock_client:
            mock_client.containers.get.return_value = mock_container_without_label
            
            monitor._handle_container_start("container123")
            
            mock_client.containers.get.assert_called_once_with("container123")
            dns_callback.assert_not_called()

    def test_handle_container_stop_with_label(self, monitor, dns_callback, mock_container_with_label):
        """Test container stop event with joyride.host.name label."""
        with patch.object(monitor, 'client') as mock_client:
            mock_client.containers.get.return_value = mock_container_with_label
            
            monitor._handle_container_stop("container123")
            
            mock_client.containers.get.assert_called_once_with("container123")
            dns_callback.assert_called_once_with("remove", "test.example.com", "")

    def test_handle_container_stop_without_label(self, monitor, dns_callback, mock_container_without_label):
        """Test container stop event without joyride.host.name label."""
        with patch.object(monitor, 'client') as mock_client:
            mock_client.containers.get.return_value = mock_container_without_label
            
            monitor._handle_container_stop("container123")
            
            mock_client.containers.get.assert_called_once_with("container123")
            dns_callback.assert_not_called()

    def test_handle_container_event_start_actions(self, monitor):
        """Test container event handling for start actions."""
        with patch.object(monitor, '_handle_container_start') as mock_start:
            # Test start action
            event = {"Action": "start", "id": "container123"}
            monitor._handle_container_event(event)
            mock_start.assert_called_once_with("container123")

            mock_start.reset_mock()
            
            # Test unpause action
            event = {"Action": "unpause", "id": "container456"}
            monitor._handle_container_event(event)
            mock_start.assert_called_once_with("container456")

    def test_handle_container_event_stop_actions(self, monitor):
        """Test container event handling for stop actions."""
        with patch.object(monitor, '_handle_container_stop') as mock_stop:
            stop_actions = ["stop", "die", "pause", "destroy"]
            
            for action in stop_actions:
                event = {"Action": action, "id": f"container-{action}"}
                monitor._handle_container_event(event)
                mock_stop.assert_called_with(f"container-{action}")
            
            assert mock_stop.call_count == len(stop_actions)

    def test_handle_container_event_no_container_id(self, monitor):
        """Test container event handling with missing container ID."""
        with patch.object(monitor, '_handle_container_start') as mock_start, \
             patch.object(monitor, '_handle_container_stop') as mock_stop:
            
            event = {"Action": "start"}  # Missing "id"
            monitor._handle_container_event(event)
            
            mock_start.assert_not_called()
            mock_stop.assert_not_called()

    def test_handle_container_event_ignored_actions(self, monitor):
        """Test container event handling for ignored actions."""
        with patch.object(monitor, '_handle_container_start') as mock_start, \
             patch.object(monitor, '_handle_container_stop') as mock_stop:
            
            ignored_actions = ["create", "restart", "rename", "update"]
            
            for action in ignored_actions:
                event = {"Action": action, "id": "container123"}
                monitor._handle_container_event(event)
            
            mock_start.assert_not_called()
            mock_stop.assert_not_called()

    def test_get_container_hostname_with_label(self, monitor, mock_container_with_label):
        """Test hostname extraction with joyride.host.name label."""
        hostname = monitor._get_container_hostname(mock_container_with_label)
        assert hostname == "test.example.com"

    def test_get_container_hostname_without_label(self, monitor, mock_container_without_label):
        """Test hostname extraction without joyride.host.name label."""
        hostname = monitor._get_container_hostname(mock_container_without_label)
        assert hostname is None

    def test_get_container_ip_bridge_network(self, monitor, mock_container_with_label):
        """Test IP extraction from bridge network."""
        ip = monitor._get_container_ip(mock_container_with_label)
        assert ip == "172.17.0.2"

    def test_get_container_ip_fallback_network(self, monitor):
        """Test IP extraction from non-bridge network."""
        container = Mock()
        container.attrs = {
            "NetworkSettings": {
                "Networks": {
                    "custom_network": {
                        "IPAddress": "192.168.1.100"
                    }
                }
            }
        }
        
        ip = monitor._get_container_ip(container)
        assert ip == "192.168.1.100"

    def test_get_container_ip_no_networks(self, monitor):
        """Test IP extraction with no networks."""
        container = Mock()
        container.attrs = {
            "NetworkSettings": {
                "Networks": {}
            }
        }
        
        ip = monitor._get_container_ip(container)
        assert ip is None

    def test_process_existing_containers(self, monitor, dns_callback):
        """Test processing existing containers on startup."""
        mock_container1 = Mock()
        mock_container1.attrs = {
            "Config": {"Labels": {"joyride.host.name": "app1.local"}},
            "NetworkSettings": {"Networks": {"bridge": {"IPAddress": "172.17.0.10"}}}
        }
        
        mock_container2 = Mock()
        mock_container2.attrs = {
            "Config": {"Labels": {}},  # No joyride label
            "NetworkSettings": {"Networks": {"bridge": {"IPAddress": "172.17.0.11"}}}
        }
        
        mock_container3 = Mock()
        mock_container3.attrs = {
            "Config": {"Labels": {"joyride.host.name": "app2.local"}},
            "NetworkSettings": {"Networks": {"bridge": {"IPAddress": "172.17.0.12"}}}
        }
        
        with patch.object(monitor, 'client') as mock_client:
            mock_client.containers.list.return_value = [mock_container1, mock_container2, mock_container3]
            
            monitor._process_existing_containers()
            
            mock_client.containers.list.assert_called_once_with(filters={"status": "running"})
            
            # Should only call DNS callback for containers with joyride labels
            expected_calls = [
                call("add", "app1.local", "172.17.0.10"),
                call("add", "app2.local", "172.17.0.12")
            ]
            dns_callback.assert_has_calls(expected_calls, any_order=True)
            assert dns_callback.call_count == 2

    def test_container_start_error_handling(self, monitor, dns_callback):
        """Test error handling in container start event."""
        with patch.object(monitor, 'client') as mock_client:
            mock_client.containers.get.side_effect = Exception("Container not found")
            
            monitor._handle_container_start("nonexistent")
            
            dns_callback.assert_not_called()

    def test_container_stop_error_handling(self, monitor, dns_callback):
        """Test error handling in container stop event."""
        with patch.object(monitor, 'client') as mock_client:
            mock_client.containers.get.side_effect = Exception("Container not found")
            
            monitor._handle_container_stop("nonexistent")
            
            dns_callback.assert_not_called()

    @patch('docker.from_env')
    def test_start_monitor(self, mock_docker_from_env, monitor, dns_callback):
        """Test starting the Docker monitor."""
        mock_client = Mock()
        mock_docker_from_env.return_value = mock_client
        
        with patch.object(monitor, '_process_existing_containers') as mock_process, \
             patch('threading.Thread') as mock_thread:
            
            monitor.start()
            
            mock_docker_from_env.assert_called_once()
            mock_process.assert_called_once()
            mock_thread.assert_called_once()
            assert monitor.client == mock_client

    def test_start_monitor_already_running(self, monitor):
        """Test starting monitor when already running."""
        monitor.monitor_thread = Mock()  # Simulate already running
        
        with patch('docker.from_env') as mock_docker_from_env:
            monitor.start()
            mock_docker_from_env.assert_not_called()

    def test_stop_monitor(self, monitor):
        """Test stopping the Docker monitor."""
        mock_thread = Mock()
        mock_client = Mock()
        monitor.monitor_thread = mock_thread
        monitor.client = mock_client
        monitor._stop_event = Mock()

        monitor.stop()

        monitor._stop_event.set.assert_called_once()
        mock_client.close.assert_called_once()
        assert monitor.client is None
        assert monitor.monitor_thread is None

    def test_stop_monitor_not_running(self, monitor):
        """Test stopping monitor when not running."""
        # Should not raise exception
        monitor.stop()
