"""
Tests for DNS Sync Manager Integration

This module tests the integration between swimmies SWIM protocol
and Joyride DNS service for automatic DNS record distribution.
"""

import time
from unittest.mock import Mock, patch

import pytest

from app.dns_sync_manager import DNSSyncManager


class TestDNSSyncManager:
    """Test DNS synchronization manager functionality."""

    def test_dns_sync_manager_initialization(self):
        """Test DNS sync manager can be initialized."""
        dns_callback = Mock()
        
        sync_manager = DNSSyncManager(
            node_id="test-node-1",
            service_name="test-dns",
            discovery_port=8889,
            swim_port=8890,
            dns_callback=dns_callback,
            host_ip="127.0.0.1"
        )
        
        assert sync_manager.node_id == "test-node-1"
        assert sync_manager.service_name == "test-dns"
        assert sync_manager.discovery_port == 8889
        assert sync_manager.swim_port == 8890
        assert sync_manager.dns_callback == dns_callback
        assert sync_manager.host_ip == "127.0.0.1"
        assert not sync_manager.running

    def test_dns_record_management(self):
        """Test adding and removing DNS records."""
        dns_callback = Mock()
        
        sync_manager = DNSSyncManager(
            node_id="test-node-1",
            dns_callback=dns_callback,
            host_ip="127.0.0.1"
        )
        
        # Test adding a DNS record
        sync_manager.add_dns_record("test.local", "1.2.3.4")
        
        # Verify record was added locally
        records = sync_manager.get_dns_records()
        assert "test.local" in records
        assert records["test.local"]["value"] == "1.2.3.4"
        assert records["test.local"]["type"] == "A"
        
        # Verify callback was called
        dns_callback.assert_called_with("add", "test.local", "1.2.3.4")
        
        # Test removing the DNS record
        dns_callback.reset_mock()
        sync_manager.remove_dns_record("test.local")
        
        # Verify record was removed
        records = sync_manager.get_dns_records()
        assert "test.local" not in records
        
        # Verify callback was called
        dns_callback.assert_called_with("remove", "test.local", "")

    def test_cluster_status(self):
        """Test getting cluster status information."""
        sync_manager = DNSSyncManager(
            node_id="test-node-1",
            host_ip="127.0.0.1"
        )
        
        status = sync_manager.get_cluster_status()
        
        assert status["node_id"] == "test-node-1"
        assert status["running"] == False
        assert "statistics" in status
        assert status["statistics"]["nodes_discovered"] == 0
        assert status["statistics"]["dns_records_synced"] == 0

    @patch('app.dns_sync_manager.NodeDiscovery')
    @patch('app.dns_sync_manager.create_swim_node')
    def test_start_stop_lifecycle(self, mock_create_swim, mock_node_discovery):
        """Test starting and stopping the DNS sync manager."""
        # Mock the swimmies components
        mock_discovery_instance = Mock()
        mock_swim_instance = Mock()
        
        mock_node_discovery.return_value = mock_discovery_instance
        mock_create_swim.return_value = mock_swim_instance
        
        sync_manager = DNSSyncManager(
            node_id="test-node-1",
            host_ip="127.0.0.1"
        )
        
        # Test start
        sync_manager.start()
        
        assert sync_manager.running
        mock_discovery_instance.start.assert_called_once()
        mock_swim_instance.start.assert_called_once()
        
        # Test stop
        sync_manager.stop()
        
        assert not sync_manager.running
        mock_swim_instance.stop.assert_called_once()
        mock_discovery_instance.stop.assert_called_once()

    def test_dns_sync_callback(self):
        """Test DNS sync from remote nodes."""
        dns_callback = Mock()
        
        sync_manager = DNSSyncManager(
            node_id="test-node-1",
            dns_callback=dns_callback,
            host_ip="127.0.0.1"
        )
        
        # Simulate receiving DNS records from another node
        remote_records = {
            "remote.local": {
                "type": "A",
                "value": "10.0.0.1",
                "ttl": 300,
                "timestamp": time.time(),
                "source": "remote-node"
            }
        }
        
        sync_manager._on_dns_sync_received(remote_records)
        
        # Verify records were merged locally
        local_records = sync_manager.get_dns_records()
        assert "remote.local" in local_records
        assert local_records["remote.local"]["value"] == "10.0.0.1"
        
        # Verify callback was called to update local DNS server
        dns_callback.assert_called_with("add", "remote.local", "10.0.0.1")

    def test_force_sync(self):
        """Test forcing DNS synchronization."""
        sync_manager = DNSSyncManager(
            node_id="test-node-1",
            host_ip="127.0.0.1"
        )
        
        # Add some local records
        sync_manager.add_dns_record("local.test", "192.168.1.1")
        
        # Mock SWIM protocol
        mock_swim = Mock()
        sync_manager.swim_protocol = mock_swim
        
        # Force sync
        sync_manager.force_sync()
        
        # Verify SWIM protocol was called to sync records
        mock_swim.add_dns_record.assert_called()
        
        # Verify statistics were updated
        assert sync_manager.stats["sync_operations"] > 0

    def test_node_discovery_callbacks(self):
        """Test handling of node discovery events."""
        sync_manager = DNSSyncManager(node_id="test-node-1", host_ip="127.0.0.1")

        # Mock node info - create a simple mock object with required attributes
        node_info = Mock()
        node_info.node_id = "remote-node"
        node_info.hostname = "remote-host"
        node_info.ip_address = "10.0.0.2"
        node_info.port = 8889
        node_info.service_type = "joyride-dns"
        node_info.metadata = {"swim_port": 8890, "role": "dns-server"}

        # Mock SWIM protocol
        mock_swim = Mock()
        sync_manager.swim_protocol = mock_swim

        # Test node discovered callback
        sync_manager._on_node_discovered(node_info)

        # Verify statistics were updated
        assert sync_manager.stats["nodes_discovered"] == 1

        # Verify SWIM join was attempted
        mock_swim.join_cluster.assert_called_with(["10.0.0.2:8890"])

        # Test node left callback
        sync_manager._on_node_left(node_info)

        # Verify statistics were updated
        assert sync_manager.stats["nodes_discovered"] == 0


if __name__ == "__main__":
    pytest.main([__file__])
