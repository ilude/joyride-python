"""
Tests to prevent circular dependency issues from being reintroduced.

This module specifically tests the fixes for the circular callback dependency
issue that was caused by self-referential Docker container labels.
"""

import threading
import time
from collections import defaultdict
from unittest.mock import MagicMock, Mock, call, patch

from app.dns_sync_manager import DNSSyncManager
from app.docker_monitor import DockerEventMonitor


class CallTracker:
    """Helper class to track function calls and detect infinite recursion."""
    
    def __init__(self, max_calls=10):
        self.calls = defaultdict(int)
        self.call_stack = []
        self.max_calls = max_calls
        
    def track_call(self, function_name: str, *args, **kwargs):
        """Track a function call and detect potential infinite recursion."""
        self.calls[function_name] += 1
        self.call_stack.append(function_name)
        
        # Keep only recent calls in stack for analysis
        if len(self.call_stack) > 20:
            self.call_stack = self.call_stack[-10:]
            
        # Check for excessive calls to same function
        if self.calls[function_name] > self.max_calls:
            raise RecursionError(
                f"Potential infinite recursion detected: {function_name} "
                f"called {self.calls[function_name]} times. "
                f"Recent call stack: {self.call_stack[-10:]}"
            )
    
    def reset(self):
        """Reset call tracking."""
        self.calls.clear()
        self.call_stack.clear()


class TestCircularDependencyPrevention:
    """Test circular dependency prevention mechanisms."""

    def test_dns_sync_manager_local_only_parameter(self):
        """Test that local_only parameter prevents callback loops."""
        callback_tracker = CallTracker(max_calls=5)
        
        def tracked_dns_callback(action: str, hostname: str, ip_address: str):
            """DNS callback that tracks calls to detect loops."""
            callback_tracker.track_call("dns_callback", action, hostname, ip_address)
            
            # Simulate what the real callback does - it would normally
            # call back to DNS sync manager without local_only protection
            if action == "add":
                # This would create infinite loop without local_only protection
                pass
            
        sync_manager = DNSSyncManager(
            node_id="test-node-1",
            dns_callback=tracked_dns_callback,
            host_ip="127.0.0.1"
        )
        
        # Test 1: Normal operation should call callback
        callback_tracker.reset()
        sync_manager.add_dns_record("test.example.com", "1.2.3.4")
        assert callback_tracker.calls["dns_callback"] == 1
        
        # Test 2: local_only=True should NOT call callback
        callback_tracker.reset()
        sync_manager.add_dns_record("test2.example.com", "1.2.3.5", local_only=True)
        assert callback_tracker.calls["dns_callback"] == 0
        
        # Test 3: Multiple local_only calls should not accumulate callbacks
        callback_tracker.reset()
        for i in range(5):
            sync_manager.add_dns_record(f"test{i}.example.com", f"1.2.3.{i}", local_only=True)
        assert callback_tracker.calls["dns_callback"] == 0
        
        # Test 4: Remove operations with local_only
        callback_tracker.reset()
        sync_manager.remove_dns_record("test.example.com", local_only=True)
        assert callback_tracker.calls["dns_callback"] == 0

    def test_dns_record_callback_prevents_infinite_loop(self):
        """Test that dns_record_callback uses local_only to prevent loops."""
        from app.main import dns_record_callback, dns_server, dns_sync_manager

        # Mock the DNS server and sync manager
        with patch.object(dns_server, 'add_record') as mock_dns_add, \
             patch.object(dns_server, 'remove_record') as mock_dns_remove:
            
            if dns_sync_manager:
                with patch.object(dns_sync_manager, 'add_dns_record') as mock_sync_add, \
                     patch.object(dns_sync_manager, 'remove_dns_record') as mock_sync_remove, \
                     patch.object(dns_sync_manager, 'running', True):
                    
                    # Test add operation
                    dns_record_callback("add", "test.example.com", "1.2.3.4")
                    
                    # Verify DNS server was called
                    mock_dns_add.assert_called_once_with("test.example.com", "1.2.3.4")
                    
                    # Verify DNS sync manager was called with local_only=True
                    mock_sync_add.assert_called_once_with("test.example.com", "1.2.3.4", local_only=True)
                    
                    # Test remove operation
                    dns_record_callback("remove", "test.example.com", "1.2.3.4")
                    
                    # Verify DNS server was called
                    mock_dns_remove.assert_called_once_with("test.example.com")
                    
                    # Verify DNS sync manager was called with local_only=True
                    mock_sync_remove.assert_called_once_with("test.example.com", local_only=True)

    def test_docker_monitor_self_referential_container_safety(self):
        """Test that Docker monitor safely handles self-referential containers."""
        callback_tracker = CallTracker(max_calls=3)
        
        def tracked_callback(action: str, hostname: str, ip_address: str):
            """Callback that tracks calls to detect infinite loops."""
            callback_tracker.track_call("docker_callback", action, hostname, ip_address)
        
        # Create a mock Docker client
        mock_docker_client = MagicMock()
        
        # Create a mock container that represents the joyride container itself
        # This simulates the self-referential scenario that caused the original issue
        self_referential_container = MagicMock()
        self_referential_container.attrs = {
            'Config': {
                'Labels': {
                    'joyride.host.name': 'joyride.example.com',  # Self-referential label
                    'joyride.enabled': 'true'
                }
            },
            'NetworkSettings': {
                'Networks': {
                    'bridge': {
                        'IPAddress': '172.17.0.2'
                    }
                }
            },
            'Name': '/joyride-container'
        }
        
        mock_docker_client.containers.list.return_value = [self_referential_container]
        
        with patch('docker.from_env', return_value=mock_docker_client):
            monitor = DockerEventMonitor(tracked_callback, "172.17.0.2")
            
            # Process the self-referential container
            # This should NOT cause infinite recursion
            callback_tracker.reset()
            monitor.process_existing_containers()
            
            # Should call callback exactly once, not enter infinite loop
            assert callback_tracker.calls["docker_callback"] <= 1
            
            # If callback was called, verify it was with correct parameters
            if callback_tracker.calls["docker_callback"] == 1:
                # The callback should have been called with the container's hostname
                pass  # We just verify no infinite recursion occurred

    def test_integration_scenario_no_circular_dependency(self):
        """Test full integration scenario that previously caused circular dependency."""
        callback_tracker = CallTracker(max_calls=5)
        
        # Create a mock scenario that simulates the problematic case:
        # 1. Docker monitor processes a container with joyride.host.name label
        # 2. Calls dns_record_callback
        # 3. dns_record_callback calls dns_sync_manager with local_only=True
        # 4. Should NOT call back to dns_record_callback
        
        def tracked_dns_callback(action: str, hostname: str, ip_address: str):
            """DNS callback that tracks calls and simulates the full callback chain."""
            callback_tracker.track_call("dns_record_callback", action, hostname, ip_address)
            
            # Simulate what dns_record_callback does
            if action == "add":
                # This would normally call dns_sync_manager.add_dns_record with local_only=True
                callback_tracker.track_call("dns_sync_add_local_only", hostname, ip_address)
            elif action == "remove":
                callback_tracker.track_call("dns_sync_remove_local_only", hostname, ip_address)
        
        # Create DNS sync manager with the tracked callback
        sync_manager = DNSSyncManager(
            node_id="test-integration-node",
            dns_callback=tracked_dns_callback,
            host_ip="172.17.0.2"
        )
        
        # Simulate the problematic sequence:
        # 1. Container event triggers callback
        callback_tracker.reset()
        
        # 2. DNS record callback is triggered (simulating Docker monitor)
        tracked_dns_callback("add", "joyride.example.com", "172.17.0.2")
        
        # 3. DNS sync manager operation with local_only=True (should not trigger callback)
        sync_manager.add_dns_record("joyride.example.com", "172.17.0.2", local_only=True)
        
        # Verify the sequence completed without infinite recursion
        assert callback_tracker.calls["dns_record_callback"] == 1
        assert callback_tracker.calls["dns_sync_add_local_only"] == 1
        
        # The sync manager operation with local_only should not have triggered
        # another callback, proving the circular dependency is broken

    def test_concurrent_dns_operations_no_deadlock(self):
        """Test that concurrent DNS operations don't cause deadlocks."""
        callback_tracker = CallTracker(max_calls=50)
        results = []
        
        def thread_safe_callback(action: str, hostname: str, ip_address: str):
            """Thread-safe callback for concurrent testing."""
            callback_tracker.track_call(f"callback_{threading.current_thread().ident}")
            results.append((action, hostname, ip_address))
        
        sync_manager = DNSSyncManager(
            node_id="test-concurrent-node",
            dns_callback=thread_safe_callback,
            host_ip="127.0.0.1"
        )
        
        def worker(thread_id: int):
            """Worker function for concurrent operations."""
            for i in range(5):
                # Normal operations
                sync_manager.add_dns_record(f"test{thread_id}-{i}.example.com", f"10.0.{thread_id}.{i}")
                
                # Local-only operations (should not trigger callbacks)
                sync_manager.add_dns_record(f"local{thread_id}-{i}.example.com", f"10.1.{thread_id}.{i}", local_only=True)
                
                time.sleep(0.001)  # Small delay to encourage race conditions
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)  # 5 second timeout to prevent hanging
            assert not thread.is_alive(), "Thread did not complete within timeout"
        
        # Verify operations completed without deadlock
        # Should have 3 threads * 5 normal operations = 15 callbacks
        # Local-only operations should not trigger callbacks
        assert len(results) == 15
        
        # Verify no excessive recursive calls occurred
        for func_name, call_count in callback_tracker.calls.items():
            assert call_count <= 10, f"Excessive calls to {func_name}: {call_count}"

    def test_edge_cases_preventing_regression(self):
        """Test edge cases that could lead to regression of the circular dependency fix."""
        
        # Test case 1: DNS sync manager not running
        sync_manager = DNSSyncManager(
            node_id="test-edge-node",
            dns_callback=Mock(),
            host_ip="127.0.0.1"
        )
        
        # Should not crash when not running
        sync_manager.add_dns_record("test.example.com", "1.2.3.4", local_only=True)
        sync_manager.remove_dns_record("test.example.com", local_only=True)
        
        # Test case 2: None callback
        sync_manager_no_callback = DNSSyncManager(
            node_id="test-no-callback",
            dns_callback=None,
            host_ip="127.0.0.1"
        )
        
        # Should not crash with None callback
        sync_manager_no_callback.add_dns_record("test.example.com", "1.2.3.4")
        sync_manager_no_callback.add_dns_record("test.example.com", "1.2.3.4", local_only=True)
        
        # Test case 3: Empty hostname
        sync_manager.add_dns_record("", "1.2.3.4", local_only=True)
        sync_manager.remove_dns_record("", local_only=True)
        
        # Test case 4: Invalid IP addresses
        sync_manager.add_dns_record("test.example.com", "invalid-ip", local_only=True)

    def test_dns_sync_manager_callback_isolation(self):
        """Test that DNS sync manager properly isolates callback operations."""
        primary_callback = Mock()
        
        sync_manager = DNSSyncManager(
            node_id="test-isolation",
            dns_callback=primary_callback,
            host_ip="127.0.0.1"
        )
        
        # Normal operation should trigger callback
        sync_manager.add_dns_record("normal.example.com", "1.2.3.4")
        assert primary_callback.call_count == 1
        primary_callback.assert_called_with("add", "normal.example.com", "1.2.3.4")
        
        # local_only operation should NOT trigger callback
        primary_callback.reset_mock()
        sync_manager.add_dns_record("local.example.com", "1.2.3.5", local_only=True)
        assert primary_callback.call_count == 0
        
        # Remove operation should trigger callback
        sync_manager.remove_dns_record("normal.example.com")
        assert primary_callback.call_count == 1
        primary_callback.assert_called_with("remove", "normal.example.com", "")
        
        # local_only remove should NOT trigger callback
        primary_callback.reset_mock()
        sync_manager.remove_dns_record("local.example.com", local_only=True)
        assert primary_callback.call_count == 0

    def test_circular_dependency_fix_backward_compatibility(self):
        """Test that the circular dependency fix maintains backward compatibility."""
        callback = Mock()
        
        sync_manager = DNSSyncManager(
            node_id="test-compat",
            dns_callback=callback,
            host_ip="127.0.0.1"
        )
        
        # Test that existing code without local_only parameter still works
        sync_manager.add_dns_record("compat.example.com", "1.2.3.4")
        assert callback.call_count == 1
        
        sync_manager.remove_dns_record("compat.example.com")
        assert callback.call_count == 2
        
        # Test that the new local_only parameter is optional
        sync_manager.add_dns_record("compat2.example.com", "1.2.3.5", local_only=False)
        assert callback.call_count == 3
        
        # Verify the calls were made with correct parameters
        expected_calls = [
            call("add", "compat.example.com", "1.2.3.4"),
            call("remove", "compat.example.com", ""),
            call("add", "compat2.example.com", "1.2.3.5")
        ]
        callback.assert_has_calls(expected_calls)
