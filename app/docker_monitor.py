import logging
import threading
from typing import Any, Callable, Dict, Optional

import docker
from docker.errors import DockerException

logger = logging.getLogger(__name__)


class DockerEventMonitor:
    """Monitors Docker container events and manages DNS records."""

    def __init__(self, dns_callback: Callable[[str, str, str], None]):
        """
        Initialize Docker event monitor.

        Args:
            dns_callback: Callback function (action, hostname, ip_address)
                         action: 'add' or 'remove'
        """
        self.dns_callback = dns_callback
        self.client: Optional[docker.DockerClient] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start monitoring Docker events."""
        if self.monitor_thread is not None:
            logger.warning("Docker monitor already running")
            return

        try:
            self.client = docker.from_env()
            self.client.ping()  # Test connection

            # Process existing containers first
            self._process_existing_containers()

            # Start event monitoring thread
            self.monitor_thread = threading.Thread(
                target=self._monitor_events, daemon=True
            )
            self.monitor_thread.start()

            logger.info("Docker event monitor started")
        except DockerException as e:
            logger.error(f"Failed to connect to Docker: {e}")
            raise

    def stop(self) -> None:
        """Stop monitoring Docker events."""
        self._stop_event.set()
        if self.client:
            self.client.close()
            self.client = None
        self.monitor_thread = None
        logger.info("Docker event monitor stopped")

    def _monitor_events(self) -> None:
        """Monitor Docker events in background thread."""
        try:
            for event in self.client.events(decode=True):
                if self._stop_event.is_set():
                    break

                if event.get("Type") == "container":
                    self._handle_container_event(event)
        except Exception as e:
            if not self._stop_event.is_set():
                logger.error(f"Docker event monitoring error: {e}")

    def _handle_container_event(self, event: Dict[str, Any]) -> None:
        """Handle container lifecycle events."""
        action = event.get("Action")
        container_id = event.get("id")

        if not container_id:
            return

        if action in ("start", "unpause"):
            self._handle_container_start(container_id)
        elif action in ("stop", "die", "pause", "destroy"):
            self._handle_container_stop(container_id)

    def _handle_container_start(self, container_id: str) -> None:
        """Handle container start event."""
        try:
            container = self.client.containers.get(container_id)
            hostname = self._get_container_hostname(container)

            if hostname:
                ip_address = self._get_container_ip(container)
                if ip_address:
                    self.dns_callback("add", hostname, ip_address)
                    logger.info(f"Container started: {hostname} -> {ip_address}")
        except Exception as e:
            logger.error(f"Error handling container start {container_id}: {e}")

    def _handle_container_stop(self, container_id: str) -> None:
        """Handle container stop event."""
        try:
            container = self.client.containers.get(container_id)
            hostname = self._get_container_hostname(container)

            if hostname:
                self.dns_callback("remove", hostname, "")
                logger.info(f"Container stopped: removed {hostname}")
        except Exception as e:
            logger.debug(f"Error handling container stop {container_id}: {e}")

    def _process_existing_containers(self) -> None:
        """Process already running containers on startup."""
        try:
            containers = self.client.containers.list(filters={"status": "running"})

            for container in containers:
                hostname = self._get_container_hostname(container)
                if hostname:
                    ip_address = self._get_container_ip(container)
                    if ip_address:
                        self.dns_callback("add", hostname, ip_address)
                        logger.info(f"Existing container: {hostname} -> {ip_address}")
        except Exception as e:
            logger.error(f"Error processing existing containers: {e}")

    def _get_container_hostname(self, container) -> Optional[str]:
        """Extract hostname from container labels."""
        labels = container.attrs.get("Config", {}).get("Labels", {})
        return labels.get("joyride.host.name")

    def _get_container_ip(self, container) -> Optional[str]:
        """Get container IP address from default network."""
        try:
            network_settings = container.attrs.get("NetworkSettings", {})
            networks = network_settings.get("Networks", {})

            # Try to get IP from default bridge network first
            if "bridge" in networks:
                return networks["bridge"].get("IPAddress")

            # Fall back to first available network
            for network_name, network_info in networks.items():
                ip_address = network_info.get("IPAddress")
                if ip_address:
                    return ip_address

            return None
        except Exception as e:
            logger.error(f"Error getting container IP: {e}")
            return None
