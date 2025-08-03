import logging
import threading
import time
from pathlib import Path
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class HostsFileMonitor:
    """Monitors hosts files in a directory and updates DNS records."""

    def __init__(
        self,
        hosts_directory: str,
        dns_callback: Callable[[str, str, str], None],
        poll_interval: float = 5.0,
    ):
        """Initialize the hosts file monitor.
        
        Args:
            hosts_directory: Directory containing hosts files
            dns_callback: Callback function(action, hostname, ip_address)
            poll_interval: How often to check for changes (seconds)
        """
        self.hosts_directory = Path(hosts_directory)
        self.dns_callback = dns_callback
        self.poll_interval = poll_interval
        self.monitor_thread: Optional[threading.Thread] = None
        self.running = False
        self.current_records: Dict[str, str] = {}
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start monitoring hosts files."""
        if self.running:
            logger.warning("Hosts file monitor already running")
            return

        if not self.hosts_directory.exists():
            logger.warning(f"Hosts directory {self.hosts_directory} does not exist")
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Started hosts file monitor for directory: {self.hosts_directory}")

    def stop(self) -> None:
        """Stop monitoring hosts files."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.debug("Hosts file monitor stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        # Initial load
        self._load_all_hosts_files()

        while self.running:
            try:
                self._check_for_changes()
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in hosts file monitor: {e}")
                time.sleep(self.poll_interval)

    def _check_for_changes(self) -> None:
        """Check for changes in hosts files."""
        new_records = self._load_hosts_records()
        
        with self._lock:
            # Find additions and updates
            for hostname, ip_address in new_records.items():
                if hostname not in self.current_records or self.current_records[hostname] != ip_address:
                    self.dns_callback("add", hostname, ip_address)
                    logger.debug(f"Added/updated hosts record: {hostname} -> {ip_address}")

            # Find removals
            for hostname in list(self.current_records.keys()):
                if hostname not in new_records:
                    self.dns_callback("remove", hostname, "")
                    logger.debug(f"Removed hosts record: {hostname}")

            self.current_records = new_records

    def _load_all_hosts_files(self) -> None:
        """Load all hosts files initially."""
        records = self._load_hosts_records()
        with self._lock:
            self.current_records = records
            for hostname, ip_address in records.items():
                self.dns_callback("add", hostname, ip_address)
        
        if records:
            logger.info(f"Loaded {len(records)} hosts records from files")

    def _load_hosts_records(self) -> Dict[str, str]:
        """Load DNS records from all hosts files in the directory."""
        records: Dict[str, str] = {}
        
        if not self.hosts_directory.exists():
            return records

        # Find all files in the directory (skip hidden dotfiles for security)
        for file_path in self.hosts_directory.glob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    file_records = self._parse_hosts_file(file_path)
                    records.update(file_records)
                    if file_records:
                        logger.debug(f"Loaded {len(file_records)} records from {file_path.name}")
                except Exception as e:
                    logger.error(f"Error reading hosts file {file_path}: {e}")

        return records

    def _parse_hosts_file(self, file_path: Path) -> Dict[str, str]:
        """Parse a single hosts file and return DNS records.
        
        Supports standard /etc/hosts format:
        # Comments start with #
        192.168.1.100  example.com www.example.com
        10.0.0.1       service.internal
        """
        records: Dict[str, str] = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Split on whitespace
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    
                    ip_address = parts[0]
                    hostnames = parts[1:]
                    
                    # Validate IP address format (basic check)
                    if not self._is_valid_ip(ip_address):
                        logger.warning(f"Invalid IP address '{ip_address}' in {file_path.name}:{line_num}")
                        continue
                    
                    # Add all hostnames for this IP
                    for hostname in hostnames:
                        hostname = hostname.strip()
                        if hostname:
                            records[hostname] = ip_address
                            
        except Exception as e:
            logger.error(f"Error parsing hosts file {file_path}: {e}")
            
        return records

    def _is_valid_ip(self, ip_address: str) -> bool:
        """Basic IP address validation."""
        try:
            parts = ip_address.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not (0 <= int(part) <= 255):
                    return False
            return True
        except (ValueError, AttributeError):
            return False

    def get_current_records(self) -> Dict[str, str]:
        """Get a copy of current records from hosts files."""
        with self._lock:
            return self.current_records.copy()
