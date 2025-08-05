"""
DNS Synchronization Manager for Joyride DNS Service

This module provides automatic DNS record distribution across discovered nodes
using the swimmies SWIM protocol for distributed consensus and synchronization.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from swimmies.discovery import NodeDiscovery, NodeInfo
from swimmies.swim import SwimProtocol, create_swim_node

logger = logging.getLogger(__name__)


class DNSSyncManager:
    """
    Manages DNS record synchronization across multiple Joyride DNS nodes.

    This class integrates the swimmies SWIM protocol with Joyride DNS to provide:
    - Automatic node discovery on the local network
    - Distributed DNS record synchronization
    - Failure detection and recovery
    - Consistent DNS responses across all nodes
    """

    def __init__(
        self,
        node_id: str,
        service_name: str = "joyride-dns",
        discovery_port: int = 8889,
        swim_port: int = 8890,
        dns_callback: Optional[Callable[[str, str, str], None]] = None,
        host_ip: str = "127.0.0.1",
    ):
        """
        Initialize DNS synchronization manager.

        Args:
            node_id: Unique identifier for this DNS node
            service_name: Service type for node discovery filtering
            discovery_port: UDP port for node discovery broadcasts
            swim_port: UDP port for SWIM protocol communication
            dns_callback: Callback to manage local DNS records (action, hostname, ip)
            host_ip: IP address of this node
        """
        self.node_id = node_id
        self.service_name = service_name
        self.discovery_port = discovery_port
        self.swim_port = swim_port
        self.dns_callback = dns_callback
        self.host_ip = host_ip

        # Internal state
        self.running = False
        self.local_dns_records: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        # Components
        self.node_discovery: Optional[NodeDiscovery] = None
        self.swim_protocol: Optional[SwimProtocol] = None

        # Statistics
        self.stats = {
            "nodes_discovered": 0,
            "nodes_active": 0,
            "dns_records_synced": 0,
            "sync_operations": 0,
            "last_sync": None,
        }

    def start(self) -> None:
        """Start DNS synchronization services."""
        if self.running:
            logger.warning("DNS sync manager already running")
            return

        try:
            logger.info(f"Starting DNS sync manager for node: {self.node_id}")

            # Create node info for this DNS service
            node_info = NodeInfo(
                node_id=self.node_id,
                hostname=f"joyride-{self.node_id}",
                ip_address=self.host_ip,
                port=self.discovery_port,
                service_type=self.service_name,
                last_seen=datetime.now(),
                metadata={
                    "version": "1.0.0",
                    "role": "dns-server",
                    "swim_port": self.swim_port,
                },
            )

            # Initialize node discovery
            self.node_discovery = NodeDiscovery(
                node_id=self.node_id,
                service_type=self.service_name,
                broadcast_port=self.discovery_port,
                heartbeat_interval=30,
                node_timeout=90,
                metadata=node_info.metadata,
            )

            # Set up discovery callbacks
            self.node_discovery.node_discovered_callback = self._on_node_discovered
            self.node_discovery.node_left_callback = self._on_node_left

            # Initialize SWIM protocol
            self.swim_protocol = create_swim_node(
                node_info=node_info,
                swim_port=self.swim_port,
                protocol_interval=5.0,
                suspect_timeout=15.0,
            )

            # Set up SWIM callbacks
            self.swim_protocol.member_joined_callback = self._on_swim_member_joined
            self.swim_protocol.member_failed_callback = self._on_swim_member_failed
            self.swim_protocol.dns_sync_callback = self._on_dns_sync_received

            # Start services
            self.node_discovery.start()
            self.swim_protocol.start()

            self.running = True
            logger.info("DNS sync manager started successfully")

        except Exception as e:
            logger.error(f"Failed to start DNS sync manager: {e}")
            self.stop()
            raise

    def stop(self) -> None:
        """Stop DNS synchronization services."""
        if not self.running:
            return

        logger.info("Stopping DNS sync manager")
        self.running = False

        # Stop services
        if self.swim_protocol:
            try:
                self.swim_protocol.stop()
            except Exception as e:
                logger.error(f"Error stopping SWIM protocol: {e}")

        if self.node_discovery:
            try:
                self.node_discovery.stop()
            except Exception as e:
                logger.error(f"Error stopping node discovery: {e}")

        logger.info("DNS sync manager stopped")

    def add_dns_record(
        self,
        hostname: str,
        ip_address: str,
        record_type: str = "A",
        local_only: bool = False,
    ) -> None:
        """
        Add a DNS record and synchronize it across all nodes.

        Args:
            hostname: DNS hostname
            ip_address: IP address for the record
            record_type: DNS record type (default: A)
            local_only: If True, don't call the DNS callback (prevents circular calls)
        """
        with self._lock:
            record_data = {
                "type": record_type,
                "value": ip_address,
                "ttl": 300,
                "timestamp": time.time(),
                "source": self.node_id,
            }

            self.local_dns_records[hostname] = record_data
            logger.info(f"Added DNS record: {hostname} -> {ip_address}")

            # Update local DNS server only if this is not a local_only call
            # (local_only is used when the call originates from the DNS callback to prevent circular calls)
            if not local_only and self.dns_callback:
                self.dns_callback("add", hostname, ip_address)

            # Sync to SWIM protocol for distribution
            if self.swim_protocol:
                self.swim_protocol.add_dns_record(hostname, record_data)
                self.stats["dns_records_synced"] += 1

    def remove_dns_record(self, hostname: str, local_only: bool = False) -> None:
        """
        Remove a DNS record and synchronize the removal across all nodes.

        Args:
            hostname: DNS hostname to remove
            local_only: If True, don't call the DNS callback (prevents circular calls)
        """
        with self._lock:
            if hostname in self.local_dns_records:
                del self.local_dns_records[hostname]
                logger.info(f"Removed DNS record: {hostname}")

                # Update local DNS server only if this is not a local_only call
                # (local_only is used when the call originates from the DNS callback to prevent circular calls)
                if not local_only and self.dns_callback:
                    self.dns_callback("remove", hostname, "")

                # Sync to SWIM protocol for distribution
                if self.swim_protocol:
                    self.swim_protocol.remove_dns_record(hostname)
                    self.stats["dns_records_synced"] += 1

    def get_dns_records(self) -> Dict[str, Dict[str, Any]]:
        """Get all DNS records managed by this node."""
        with self._lock:
            return self.local_dns_records.copy()

    def get_cluster_status(self) -> Dict[str, Any]:
        """Get status information about the DNS cluster."""
        status = {
            "node_id": self.node_id,
            "running": self.running,
            "statistics": self.stats.copy(),
        }

        if self.node_discovery:
            discovered_nodes = self.node_discovery.get_discovered_nodes()
            status["discovered_nodes"] = len(discovered_nodes)
            status["nodes"] = [
                {
                    "node_id": node.node_id,
                    "ip_address": node.ip_address,
                    "last_seen": node.last_seen.isoformat(),
                    "metadata": node.metadata,
                }
                for node in discovered_nodes
            ]

        if self.swim_protocol:
            alive_members = self.swim_protocol.get_alive_members()
            member_counts = self.swim_protocol.get_member_count()
            status["swim_cluster"] = {
                "alive_members": len(alive_members),
                "member_counts": member_counts,
                "dns_version": self.swim_protocol.dns_version,
            }

        return status

    def _on_node_discovered(self, node_info: NodeInfo) -> None:
        """Handle discovery of a new node."""
        logger.info(
            f"Discovered DNS node: {node_info.node_id} at {node_info.ip_address}"
        )
        self.stats["nodes_discovered"] += 1

        # If this node has SWIM port info, initiate SWIM connection
        if "swim_port" in node_info.metadata and self.swim_protocol:
            swim_port = node_info.metadata["swim_port"]
            swim_address = f"{node_info.ip_address}:{swim_port}"

            # Attempt to join the SWIM cluster via this node
            try:
                self.swim_protocol.join_cluster([swim_address])
                logger.info(f"Initiated SWIM connection to {swim_address}")
            except Exception as e:
                logger.warning(f"Failed to connect to SWIM node {swim_address}: {e}")

    def _on_node_left(self, node_info: NodeInfo) -> None:
        """Handle a node leaving the network."""
        logger.info(f"Node left: {node_info.node_id}")
        if self.stats["nodes_discovered"] > 0:
            self.stats["nodes_discovered"] -= 1

    def _on_swim_member_joined(self, node_info: NodeInfo) -> None:
        """Handle a new SWIM cluster member."""
        logger.info(f"SWIM member joined: {node_info.node_id}")
        self.stats["nodes_active"] += 1

    def _on_swim_member_failed(self, node_info: NodeInfo) -> None:
        """Handle a SWIM cluster member failure."""
        logger.warning(f"SWIM member failed: {node_info.node_id}")
        if self.stats["nodes_active"] > 0:
            self.stats["nodes_active"] -= 1

    def _on_dns_sync_received(self, dns_records: Dict[str, Dict[str, Any]]) -> None:
        """Handle DNS record synchronization from other nodes."""
        logger.info(f"Received DNS sync with {len(dns_records)} records")

        with self._lock:
            # Merge remote DNS records with local ones
            updated_records = 0
            for hostname, record_data in dns_records.items():
                # Only update if remote record is newer or we don't have it
                if hostname not in self.local_dns_records or record_data.get(
                    "timestamp", 0
                ) > self.local_dns_records.get(hostname, {}).get("timestamp", 0):
                    self.local_dns_records[hostname] = record_data
                    updated_records += 1

                    # Update local DNS server
                    if self.dns_callback and record_data.get("type") == "A":
                        self.dns_callback("add", hostname, record_data["value"])

            if updated_records > 0:
                logger.info(f"Updated {updated_records} DNS records from sync")
                self.stats["sync_operations"] += 1
                self.stats["last_sync"] = datetime.now().isoformat()

    def force_sync(self) -> None:
        """Force immediate DNS record synchronization across the cluster."""
        if not self.swim_protocol:
            logger.warning("SWIM protocol not available for sync")
            return

        logger.info("Forcing DNS record synchronization")

        # Trigger anti-entropy mechanism in SWIM protocol
        # This will cause all nodes to exchange their full DNS state
        try:
            # Get current DNS records and push them through SWIM
            with self._lock:
                for hostname, record_data in self.local_dns_records.items():
                    self.swim_protocol.add_dns_record(hostname, record_data)

            self.stats["sync_operations"] += 1
            logger.info("Forced DNS synchronization completed")

        except Exception as e:
            logger.error(f"Error during forced sync: {e}")
