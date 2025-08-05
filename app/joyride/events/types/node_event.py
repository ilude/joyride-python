"""Node-related event definitions for the Joyride DNS Service."""

from datetime import datetime
from typing import Any, Dict, Optional

from ..event import Event


class NodeEvent(Event):
    """SWIM cluster membership events."""

    def __init__(
        self,
        event_type: str,
        source: str,
        node_id: str,
        node_address: str,
        node_port: int,
        node_state: str,
        cluster_size: Optional[int] = None,
        node_metadata: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialize node event.

        Args:
            event_type: Type of node event
            source: Source component generating the event
            node_id: Unique node identifier
            node_address: Node IP address
            node_port: Node port number
            node_state: Node state (alive, suspected, failed, left)
            cluster_size: Current cluster size
            node_metadata: Node-specific metadata
            data: Additional event data
            metadata: Additional event metadata
            timestamp: Event timestamp
        """
        event_data = data or {}
        event_data.update(
            {
                "node_id": node_id,
                "node_address": node_address,
                "node_port": node_port,
                "node_state": node_state,
                "cluster_size": cluster_size,
                "node_metadata": node_metadata or {},
            }
        )

        super().__init__(
            event_type=event_type,
            source=source,
            data=event_data,
            metadata=metadata,
            timestamp=timestamp,
        )

    @property
    def node_id(self) -> str:
        """Get node ID."""
        return self.data["node_id"]

    @property
    def node_address(self) -> str:
        """Get node address."""
        return self.data["node_address"]

    @property
    def node_port(self) -> int:
        """Get node port."""
        return self.data["node_port"]

    @property
    def node_state(self) -> str:
        """Get node state."""
        return self.data["node_state"]

    @property
    def cluster_size(self) -> Optional[int]:
        """Get cluster size."""
        return self.data["cluster_size"]

    @property
    def node_metadata(self) -> Dict[str, Any]:
        """Get node metadata."""
        return self.data["node_metadata"]

    def _validate(self) -> None:
        """Validate node event data."""
        super()._validate()

        if not self.node_id:
            raise ValueError("Node ID cannot be empty")

        if not self.node_address:
            raise ValueError("Node address cannot be empty")

        if not isinstance(self.node_port, int) or self.node_port <= 0:
            raise ValueError("Node port must be a positive integer")

        if not self.node_state:
            raise ValueError("Node state cannot be empty")
