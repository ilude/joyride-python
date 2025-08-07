"""SWIM protocol event definitions for event producers."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.joyride.events.event import Event


class SWIMEventType(str, Enum):
    """SWIM protocol event types."""

    # Node events
    NODE_JOIN = "swim.node.join"
    NODE_LEAVE = "swim.node.leave"
    NODE_FAILED = "swim.node.failed"
    NODE_SUSPECT = "swim.node.suspect"
    NODE_ALIVE = "swim.node.alive"
    NODE_DEAD = "swim.node.dead"
    NODE_UPDATE = "swim.node.update"
    NODE_TIMEOUT = "swim.node.timeout"

    # Membership events
    MEMBERSHIP_UPDATE = "swim.membership.update"
    MEMBERSHIP_SYNC = "swim.membership.sync"
    MEMBERSHIP_CONFLICT = "swim.membership.conflict"
    MEMBERSHIP_PRUNE = "swim.membership.prune"

    # Protocol events
    PROTOCOL_PING = "swim.protocol.ping"
    PROTOCOL_PING_REQ = "swim.protocol.ping_req"
    PROTOCOL_ACK = "swim.protocol.ack"
    PROTOCOL_NACK = "swim.protocol.nack"
    PROTOCOL_INDIRECT_PING = "swim.protocol.indirect_ping"

    # Failure detection events
    FAILURE_DETECTION_TIMEOUT = "swim.failure.detection.timeout"
    FAILURE_DETECTION_RESOLVED = "swim.failure.detection.resolved"
    FAILURE_DETECTION_ESCALATED = "swim.failure.detection.escalated"

    # Gossip events
    GOSSIP_MESSAGE = "swim.gossip.message"
    GOSSIP_PROPAGATION = "swim.gossip.propagation"
    GOSSIP_DISSEMINATION = "swim.gossip.dissemination"


class SWIMNodeState(str, Enum):
    """SWIM node states."""
    ALIVE = "alive"
    SUSPECTED = "suspected"
    DEAD = "dead"
    LEFT = "left"


class SWIMEvent(Event):
    """Base class for SWIM events."""

    def __init__(
        self,
        event_type: str,
        source: str,
        swim_event_type: SWIMEventType,
        node_id: str,
        **kwargs
    ):
        """Initialize SWIM event."""
        self.swim_event_type = swim_event_type
        self.node_id = node_id

        # Extract event-specific parameters and add to data
        event_data = kwargs.pop("data", {})
        
        # Move all extra kwargs into the data dict
        for key, value in list(kwargs.items()):
            if key not in ["event_id", "timestamp", "metadata"]:
                event_data[key] = kwargs.pop(key)
        
        event_data.update({
            "swim_event_type": swim_event_type.value,
            "node_id": node_id,
        })

        super().__init__(
            event_type=event_type or swim_event_type.value,
            source=source,
            data=event_data,
            **kwargs
        )

    def _validate(self) -> None:
        """Validate SWIM event data."""
        super()._validate()
        if not self.swim_event_type:
            raise ValueError("swim_event_type cannot be empty")
        if not self.node_id:
            raise ValueError("node_id cannot be empty")


class SWIMNodeEvent(SWIMEvent):
    """SWIM node event."""

    def __init__(
        self,
        swim_event_type: SWIMEventType,
        node_id: str,
        source: str,
        target_node_id: Optional[str] = None,
        target_node_address: Optional[str] = None,
        target_node_port: Optional[int] = None,
        target_node_state: Optional[SWIMNodeState] = None,
        event_type: Optional[str] = None,
        **kwargs
    ):
        """Initialize SWIM node event."""
        self.target_node_id = target_node_id
        self.target_node_address = target_node_address
        self.target_node_port = target_node_port
        self.target_node_state = target_node_state

        super().__init__(
            event_type=event_type or swim_event_type.value,
            source=source,
            swim_event_type=swim_event_type,
            node_id=node_id,
            target_node_id=target_node_id,
            target_node_address=target_node_address,
            target_node_port=target_node_port,
            target_node_state=target_node_state.value if target_node_state else None,
            **kwargs
        )

    def _validate(self) -> None:
        """Validate SWIM node event data."""
        super()._validate()

    @property
    def is_alive(self) -> bool:
        """Check if the target node is alive."""
        return self.target_node_state == SWIMNodeState.ALIVE

    @property
    def is_failed(self) -> bool:
        """Check if the target node has failed."""
        return self.target_node_state in (SWIMNodeState.SUSPECTED, SWIMNodeState.DEAD)

    @property
    def is_suspected(self) -> bool:
        """Check if the target node is suspected."""
        return self.target_node_state == SWIMNodeState.SUSPECTED

    @property
    def is_dead(self) -> bool:
        """Check if the target node is dead."""
        return self.target_node_state == SWIMNodeState.DEAD


class SWIMProtocolEvent(SWIMEvent):
    """SWIM protocol event."""
    
    def _validate(self) -> None:
        """Validate SWIM protocol event data."""
        super()._validate()


class SWIMFailureDetectionEvent(SWIMEvent):
    """SWIM failure detection event."""
    
    def _validate(self) -> None:
        """Validate SWIM failure detection event data."""
        super()._validate()


class SWIMGossipEvent(SWIMEvent):
    """SWIM gossip event."""
    
    def _validate(self) -> None:
        """Validate SWIM gossip event data."""
        super()._validate()


class SWIMMembershipEvent(SWIMEvent):
    """SWIM membership event."""
    
    def _validate(self) -> None:
        """Validate SWIM membership event data."""
        super()._validate()


class SWIMClusterEvent(SWIMEvent):
    """SWIM cluster event."""
    
    def _validate(self) -> None:
        """Validate SWIM cluster event data."""
        super()._validate()
