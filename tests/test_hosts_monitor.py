import os
import tempfile
import time
from pathlib import Path

from app.hosts_monitor import HostsFileMonitor


class TestHostsFileMonitor:
    """Tests for the HostsFileMonitor class."""

    def test_parse_hosts_file(self):
        """Test parsing a hosts file with various formats."""
        monitor = HostsFileMonitor("/tmp", lambda a, h, i: None)

        # Create a temporary hosts file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".hosts") as f:
            f.write(
                """# This is a comment
192.168.1.100  example.com www.example.com
10.0.0.1       service.internal

# Another comment
172.16.0.10    app.local dashboard.local
"""
            )
            hosts_file = Path(f.name)

        try:
            records = monitor._parse_hosts_file(hosts_file)

            expected = {
                "example.com": "192.168.1.100",
                "www.example.com": "192.168.1.100",
                "service.internal": "10.0.0.1",
                "app.local": "172.16.0.10",
                "dashboard.local": "172.16.0.10",
            }

            assert records == expected
        finally:
            os.unlink(hosts_file)

    def test_parse_hosts_file_with_invalid_entries(self):
        """Test parsing a hosts file with invalid entries."""
        monitor = HostsFileMonitor("/tmp", lambda a, h, i: None)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".hosts") as f:
            f.write(
                """# Valid entry
192.168.1.100  valid.com

# Invalid IP
999.999.999.999  invalid-ip.com

# Missing hostname
192.168.1.101

# Valid entry
10.0.0.1  another.valid.com
"""
            )
            hosts_file = Path(f.name)

        try:
            records = monitor._parse_hosts_file(hosts_file)

            expected = {
                "valid.com": "192.168.1.100",
                "another.valid.com": "10.0.0.1",
            }

            assert records == expected
        finally:
            os.unlink(hosts_file)

    def test_is_valid_ip(self):
        """Test IP address validation."""
        monitor = HostsFileMonitor("/tmp", lambda a, h, i: None)

        # Valid IPs
        assert monitor._is_valid_ip("192.168.1.1") is True
        assert monitor._is_valid_ip("10.0.0.1") is True
        assert monitor._is_valid_ip("172.16.0.1") is True
        assert monitor._is_valid_ip("127.0.0.1") is True
        assert monitor._is_valid_ip("0.0.0.0") is True
        assert monitor._is_valid_ip("255.255.255.255") is True

        # Invalid IPs
        assert monitor._is_valid_ip("256.1.1.1") is False
        assert monitor._is_valid_ip("192.168.1") is False
        assert monitor._is_valid_ip("192.168.1.1.1") is False
        assert monitor._is_valid_ip("not.an.ip") is False
        assert monitor._is_valid_ip("") is False

    def test_monitor_lifecycle(self):
        """Test monitor start/stop lifecycle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            callback_calls = []

            def callback(action, hostname, ip):
                callback_calls.append((action, hostname, ip))

            monitor = HostsFileMonitor(temp_dir, callback, poll_interval=0.1)

            # Create initial hosts file
            hosts_file = Path(temp_dir) / "test.hosts"
            with open(hosts_file, "w") as f:
                f.write("192.168.1.100  test.com\n")

            # Start monitor
            monitor.start()

            # Give it time to load initial records
            time.sleep(0.2)

            # Should have loaded initial record
            assert len(callback_calls) >= 1
            assert ("add", "test.com", "192.168.1.100") in callback_calls

            # Stop monitor
            monitor.stop()
            assert not monitor.running

    def test_file_changes_detection(self):
        """Test that file changes are detected and processed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            callback_calls = []

            def callback(action, hostname, ip):
                callback_calls.append((action, hostname, ip))

            monitor = HostsFileMonitor(temp_dir, callback, poll_interval=0.1)
            hosts_file = Path(temp_dir) / "test.hosts"

            # Create initial file
            with open(hosts_file, "w") as f:
                f.write("192.168.1.100  initial.com\n")

            monitor.start()
            time.sleep(0.2)  # Let initial load happen

            initial_calls = len(callback_calls)

            # Update file
            with open(hosts_file, "w") as f:
                f.write("192.168.1.100  updated.com\n192.168.1.200  new.com\n")

            # Wait for change detection
            time.sleep(0.3)

            monitor.stop()

            # Should have detected changes
            assert len(callback_calls) > initial_calls

            # Check for expected operations
            recent_calls = callback_calls[initial_calls:]
            actions = [call[0] for call in recent_calls]
            hostnames = [call[1] for call in recent_calls]

            assert "add" in actions  # New records added
            assert "updated.com" in hostnames or "new.com" in hostnames

    def test_multiple_files_loading(self):
        """Test loading records from multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            callback_calls = []

            def callback(action, hostname, ip):
                callback_calls.append((action, hostname, ip))

            # Create multiple hosts files
            file1 = Path(temp_dir) / "file1.hosts"
            file2 = Path(temp_dir) / "file2.hosts"

            with open(file1, "w") as f:
                f.write("192.168.1.100  file1.com\n")

            with open(file2, "w") as f:
                f.write("192.168.1.200  file2.com\n")

            monitor = HostsFileMonitor(temp_dir, callback, poll_interval=0.1)
            monitor.start()
            time.sleep(0.2)

            monitor.stop()

            # Should have loaded records from both files
            hostnames = [call[1] for call in callback_calls if call[0] == "add"]
            assert "file1.com" in hostnames
            assert "file2.com" in hostnames

    def test_nonexistent_directory(self):
        """Test behavior with non-existent directory."""
        callback_calls = []

        def callback(action, hostname, ip):
            callback_calls.append((action, hostname, ip))

        # Use a path that doesn't exist
        nonexistent_path = "/this/path/does/not/exist"
        monitor = HostsFileMonitor(nonexistent_path, callback)

        # Should start without error but not do anything
        monitor.start()
        time.sleep(0.1)
        monitor.stop()

        # Should not have any callback calls
        assert len(callback_calls) == 0

    def test_get_current_records(self):
        """Test getting current records."""
        with tempfile.TemporaryDirectory() as temp_dir:

            def callback(action, hostname, ip):
                pass

            monitor = HostsFileMonitor(temp_dir, callback)

            # Create hosts file
            hosts_file = Path(temp_dir) / "test.hosts"
            with open(hosts_file, "w") as f:
                f.write("192.168.1.100  test1.com\n192.168.1.200  test2.com\n")

            monitor.start()
            time.sleep(0.2)

            records = monitor.get_current_records()
            expected = {
                "test1.com": "192.168.1.100",
                "test2.com": "192.168.1.200",
            }

            assert records == expected

            monitor.stop()

    def test_hidden_files_ignored(self):
        """Test that hidden files (starting with .) are ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:

            def callback(action, hostname, ip):
                pass

            monitor = HostsFileMonitor(temp_dir, callback)

            # Create a regular hosts file
            hosts_file = Path(temp_dir) / "test.hosts"
            with open(hosts_file, "w") as f:
                f.write("192.168.1.1  test.local\n")

            # Create hidden files that should be ignored
            hidden_files = [
                Path(temp_dir) / ".gitignore",
                Path(temp_dir) / ".DS_Store",
                Path(temp_dir) / ".tmp",
            ]

            for hidden_file in hidden_files:
                with open(hidden_file, "w") as f:
                    f.write(
                        "10.0.0.1  hidden.local\n"
                    )  # Valid hosts format but should be ignored

            records = monitor._load_hosts_records()

            # Should only have the regular file's record
            assert len(records) == 1
            assert "test.local" in records
            assert "hidden.local" not in records
            assert records["test.local"] == "192.168.1.1"
