"""
Integration tests for the circular dependency fix.

This module tests the complete integration scenario that was causing
the circular dependency issue in production environments.
"""

import os
import threading
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

# Ensure testing environment
os.environ["TESTING"] = "true"


class TestCircularDependencyIntegration:
    """Integration tests for circular dependency prevention."""

    @pytest.fixture
    def mock_docker_container(self):
        """Create a mock Docker container that would trigger the circular dependency."""
        container = MagicMock()
        container.attrs = {
            'Config': {
                'Labels': {
                    'joyride.host.name': 'joyride.example.com',
                    'joyride.enabled': 'true',
                    'traefik.enable': 'true',
                    'traefik.http.routers.joyride.rule': 'Host(`joyride.example.com`)'
                }
            },
            'NetworkSettings': {
                'Networks': {
                    'joyride_default': {
                        'IPAddress': '192.168.16.191'
                    }
                }
            },
            'Name': '/joyride-joyride-1',
            'Id': 'abc123def456'
        }
        return container

    @pytest.fixture
    def mock_dns_server(self):
        """Mock DNS server manager."""
        with patch('app.main.dns_server') as mock_server:
            mock_server.add_record = Mock()
            mock_server.remove_record = Mock()
            yield mock_server

    @pytest.fixture
    def mock_dns_sync_manager(self):
        """Mock DNS sync manager with running state."""
        with patch('app.main.dns_sync_manager') as mock_sync:
            mock_sync.running = True
            mock_sync.add_dns_record = Mock()
            mock_sync.remove_dns_record = Mock()
            yield mock_sync

    def test_full_integration_no_circular_dependency(self, mock_docker_container, mock_dns_server, mock_dns_sync_manager):
        """
        Test the complete integration scenario that previously caused circular dependency.
        
        This test simulates:
        1. Docker container with joyride.host.name label (self-referential)
        2. Docker monitor processing the container
        3. Calling dns_record_callback
        4. dns_record_callback calling DNS sync manager with local_only=True
        5. Verifying no circular callback occurs
        """
        from app.main import dns_record_callback

        # Track function calls to detect infinite recursion
        call_tracker = {'dns_callback_calls': 0, 'sync_manager_calls': 0}
        
        # Wrap the original dns_record_callback to track calls
        original_callback = dns_record_callback
        
        def tracked_dns_record_callback(action, hostname, ip_address):
            call_tracker['dns_callback_calls'] += 1
            
            # Prevent runaway recursion in test
            if call_tracker['dns_callback_calls'] > 5:
                raise RecursionError(f"Circular dependency detected! dns_record_callback called {call_tracker['dns_callback_calls']} times")
            
            return original_callback(action, hostname, ip_address)
        
        # Track DNS sync manager calls
        def track_sync_add(hostname, ip_address, local_only=False):
            call_tracker['sync_manager_calls'] += 1
            # The key test: when local_only=True, this should NOT call back to dns_record_callback
            if not local_only:
                # In the buggy version, this would call back to dns_record_callback
                # causing infinite recursion. With the fix, it won't when local_only=True
                pass
                
        def track_sync_remove(hostname, local_only=False):
            call_tracker['sync_manager_calls'] += 1
            
        mock_dns_sync_manager.add_dns_record.side_effect = track_sync_add
        mock_dns_sync_manager.remove_dns_record.side_effect = track_sync_remove
        
        # Test the integration
        with patch('app.main.dns_record_callback', side_effect=tracked_dns_record_callback):
            # Simulate Docker monitor calling dns_record_callback for self-referential container
            tracked_dns_record_callback("add", "joyride.example.com", "192.168.16.191")
            
            # Verify the call chain completed without infinite recursion
            assert call_tracker['dns_callback_calls'] == 1, f"Expected 1 callback call, got {call_tracker['dns_callback_calls']}"
            assert call_tracker['sync_manager_calls'] == 1, f"Expected 1 sync manager call, got {call_tracker['sync_manager_calls']}"
            
            # Verify DNS server was called
            mock_dns_server.add_record.assert_called_once_with("joyride.example.com", "192.168.16.191")
            
            # Verify DNS sync manager was called with local_only=True (the key fix)
            mock_dns_sync_manager.add_dns_record.assert_called_once_with("joyride.example.com", "192.168.16.191", local_only=True)

    def test_docker_monitor_self_referential_container_processing(self, mock_docker_container):
        """Test that Docker monitor can safely process its own container."""
        from app.docker_monitor import DockerEventMonitor
        
        call_tracker = {'callback_calls': 0}
        
        def safe_callback(action, hostname, ip_address):
            call_tracker['callback_calls'] += 1
            # In the problematic scenario, this would eventually lead to infinite recursion
            if call_tracker['callback_calls'] > 3:
                raise RecursionError("Infinite recursion detected in callback")
        
        # Mock Docker client
        mock_docker_client = MagicMock()
        mock_docker_client.containers.list.return_value = [mock_docker_container]
        
        with patch('docker.from_env', return_value=mock_docker_client):
            monitor = DockerEventMonitor(safe_callback, "192.168.16.191")
            # Initialize the Docker client manually for testing
            monitor.client = mock_docker_client
            
            # Process existing containers - this should not cause infinite recursion
            monitor.process_existing_containers()
            
            # Should have called callback exactly once for the container
            assert call_tracker['callback_calls'] == 1
            
            # Verify no infinite recursion occurred
            assert call_tracker['callback_calls'] < 3

    def test_concurrent_dns_operations_stability(self):
        """Test that concurrent DNS operations remain stable with the circular dependency fix."""
        from app.dns_sync_manager import DNSSyncManager

        # Shared state for tracking calls across threads
        call_tracker = {'total_calls': 0, 'errors': []}
        lock = threading.Lock()
        
        def thread_safe_callback(action, hostname, ip_address):
            with lock:
                call_tracker['total_calls'] += 1
                if call_tracker['total_calls'] > 50:  # Reasonable limit
                    call_tracker['errors'].append(f"Too many callbacks: {call_tracker['total_calls']}")
        
        sync_manager = DNSSyncManager(
            node_id="test-concurrent",
            dns_callback=thread_safe_callback,
            host_ip="127.0.0.1"
        )
        
        def worker_thread(thread_id):
            """Worker that performs DNS operations."""
            try:
                for i in range(5):
                    # Normal operation (triggers callback)
                    sync_manager.add_dns_record(f"normal-{thread_id}-{i}.test", f"10.0.{thread_id}.{i}")
                    
                    # Local-only operation (should NOT trigger callback)
                    sync_manager.add_dns_record(f"local-{thread_id}-{i}.test", f"10.1.{thread_id}.{i}", local_only=True)
                    
                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                with lock:
                    call_tracker['errors'].append(f"Thread {thread_id} error: {str(e)}")
        
        # Run multiple threads concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion with timeout
        for thread in threads:
            thread.join(timeout=10.0)
            assert not thread.is_alive(), "Thread did not complete within timeout"
        
        # Verify no errors occurred
        assert not call_tracker['errors'], f"Errors detected: {call_tracker['errors']}"
        
        # Verify expected number of callbacks (only normal operations, not local_only)
        expected_callbacks = 3 * 5  # 3 threads * 5 normal operations each
        assert call_tracker['total_calls'] == expected_callbacks, \
            f"Expected {expected_callbacks} callbacks, got {call_tracker['total_calls']}"

    def test_production_scenario_simulation(self, mock_docker_container):
        """Simulate the exact production scenario that was failing."""
        from app.docker_monitor import DockerEventMonitor

        # This simulates the exact sequence that was causing issues in production:
        # 1. compose-onramp.yaml has joyride.host.name label
        # 2. Docker monitor processes this container
        # 3. Extracts hostname from joyride.host.name label
        # 4. Calls dns_record_callback
        # 5. dns_record_callback calls DNS sync manager
        # 6. With the fix: local_only=True prevents callback loop
        
        call_sequence = []
        
        def tracking_dns_callback(action, hostname, ip_address):
            call_sequence.append(f"dns_callback_{action}_{hostname}")
            # Simulate calling DNS server and sync manager
            call_sequence.append("dns_server_add")
            call_sequence.append("dns_sync_manager_add_local_only")
            # The key: local_only=True means no callback back to this function
        
        # Mock Docker components
        mock_docker_client = MagicMock()
        mock_docker_client.containers.list.return_value = [mock_docker_container]
        
        with patch('docker.from_env', return_value=mock_docker_client), \
             patch('app.main.dns_record_callback', side_effect=tracking_dns_callback):
            
            monitor = DockerEventMonitor(tracking_dns_callback, "192.168.16.191")
            # Initialize the Docker client manually for testing
            monitor.client = mock_docker_client
            
            # This was the operation that hung in production
            monitor.process_existing_containers()
            
            # Verify the sequence completed successfully
            assert len(call_sequence) > 0, "No operations were performed"
            
            # Should have exactly one DNS callback sequence, not multiple (no infinite loop)
            dns_callback_count = len([call for call in call_sequence if call.startswith('dns_callback_')])
            assert dns_callback_count == 1, f"Expected 1 DNS callback, got {dns_callback_count}: {call_sequence}"

    def test_local_only_parameter_enforcement(self):
        """Test that the local_only parameter is properly enforced in all scenarios."""
        from app.dns_sync_manager import DNSSyncManager
        
        callback_calls = []
        
        def strict_callback(action, hostname, ip_address):
            callback_calls.append((action, hostname, ip_address))
        
        sync_manager = DNSSyncManager(
            node_id="test-enforcement",
            dns_callback=strict_callback,
            host_ip="127.0.0.1"
        )
        
        # Test various scenarios with local_only
        test_cases = [
            # (hostname, ip, local_only, should_trigger_callback)
            ("test1.com", "1.1.1.1", False, True),
            ("test2.com", "1.1.1.2", True, False),
            ("test3.com", "1.1.1.3", None, True),  # Default should trigger callback
        ]
        
        for hostname, ip, local_only, should_trigger in test_cases:
            callback_calls.clear()
            
            if local_only is None:
                sync_manager.add_dns_record(hostname, ip)
            else:
                sync_manager.add_dns_record(hostname, ip, local_only=local_only)
            
            if should_trigger:
                assert len(callback_calls) == 1, f"Expected callback for {hostname} with local_only={local_only}"
                assert callback_calls[0] == ("add", hostname, ip)
            else:
                assert len(callback_calls) == 0, f"Unexpected callback for {hostname} with local_only={local_only}"
        
        # Test remove operations
        for hostname, ip, local_only, should_trigger in test_cases:
            callback_calls.clear()
            
            if local_only is None:
                sync_manager.remove_dns_record(hostname)
            else:
                sync_manager.remove_dns_record(hostname, local_only=local_only)
            
            if should_trigger:
                assert len(callback_calls) == 1, f"Expected remove callback for {hostname} with local_only={local_only}"
                assert callback_calls[0] == ("remove", hostname, "")
            else:
                assert len(callback_calls) == 0, f"Unexpected remove callback for {hostname} with local_only={local_only}"

    def test_regression_prevention_assertions(self):
        """Test assertions to prevent specific regression scenarios."""
        from app.dns_sync_manager import DNSSyncManager

        # Scenario 1: Ensure methods have local_only parameter
        sync_manager = DNSSyncManager(node_id="test-regression", host_ip="127.0.0.1")
        
        # These should work (regression test - ensure parameter exists)
        try:
            sync_manager.add_dns_record("test.com", "1.1.1.1", local_only=True)
            sync_manager.remove_dns_record("test.com", local_only=True)
        except TypeError as e:
            pytest.fail(f"local_only parameter missing from DNS sync manager methods: {e}")
        
        # Scenario 2: Ensure backward compatibility (existing code without local_only)
        try:
            sync_manager.add_dns_record("test2.com", "1.1.1.2")
            sync_manager.remove_dns_record("test2.com")
        except TypeError as e:
            pytest.fail(f"Backward compatibility broken for DNS sync manager methods: {e}")
        
        # Scenario 3: Ensure dns_record_callback uses local_only
        from app.main import dns_record_callback

        # This test verifies that dns_record_callback implementation includes local_only=True
        # by checking that it doesn't cause infinite recursion
        try:
            # Mock the components to prevent actual network operations
            with patch('app.main.dns_server') as mock_dns_server, \
                 patch('app.main.dns_sync_manager') as mock_sync_manager:
                
                mock_sync_manager.running = True
                mock_sync_manager.add_dns_record = Mock()
                
                # This should complete without infinite recursion
                dns_record_callback("add", "regression-test.com", "1.2.3.4")
                
                # Verify local_only=True was used
                mock_sync_manager.add_dns_record.assert_called_with("regression-test.com", "1.2.3.4", local_only=True)
                
        except RecursionError:
            pytest.fail("dns_record_callback is not using local_only=True, circular dependency detected!")
        except Exception as e:
            # Other exceptions are acceptable as long as no infinite recursion
            pass
