"""Docker-related event definitions for event producers."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.joyride.events.event import Event


class DockerEventType(str, Enum):
    """Docker event types."""

    CONTAINER_CREATE = "container.create"
    CONTAINER_START = "container.start"
    CONTAINER_STOP = "container.stop"
    CONTAINER_RESTART = "container.restart"
    CONTAINER_KILL = "container.kill"
    CONTAINER_PAUSE = "container.pause"
    CONTAINER_UNPAUSE = "container.unpause"
    CONTAINER_DIE = "container.die"
    CONTAINER_DESTROY = "container.destroy"
    CONTAINER_UPDATE = "container.update"
    NETWORK_CONNECT = "network.connect"
    NETWORK_DISCONNECT = "network.disconnect"
    NETWORK_CREATE = "network.create"
    NETWORK_DESTROY = "network.destroy"
    VOLUME_CREATE = "volume.create"
    VOLUME_DESTROY = "volume.destroy"
    VOLUME_MOUNT = "volume.mount"
    VOLUME_UNMOUNT = "volume.unmount"
    IMAGE_PULL = "image.pull"
    IMAGE_PUSH = "image.push"
    IMAGE_DELETE = "image.delete"
    IMAGE_TAG = "image.tag"
    IMAGE_UNTAG = "image.untag"


class DockerContainerState(str, Enum):
    """Docker container states."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    REMOVING = "removing"
    EXITED = "exited"
    DEAD = "dead"


class DockerEvent(Event):
    """Base class for all Docker events."""

    def __init__(
        self,
        event_type: str,
        source: str,
        docker_event_id: str,
        docker_event_type: DockerEventType,
        docker_timestamp: datetime,
        docker_action: str,
        actor_id: str,
        actor_type: str,
        actor_attributes: Optional[Dict[str, str]] = None,
        scope: Optional[str] = None,
        time_nano: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Initialize Docker event."""
        # Store attributes for easy access BEFORE calling super()
        self.docker_event_id = docker_event_id
        self.docker_event_type = docker_event_type
        self.docker_timestamp = docker_timestamp
        self.docker_action = docker_action
        self.actor_id = actor_id
        self.actor_type = actor_type
        self.actor_attributes = actor_attributes or {}
        self.scope = scope
        self.time_nano = time_nano

        event_data = data or {}
        event_data.update({
            "docker_event_id": docker_event_id,
            "docker_event_type": docker_event_type.value,
            "docker_timestamp": docker_timestamp.isoformat() if docker_timestamp else None,
            "docker_action": docker_action,
            "actor_id": actor_id,
            "actor_type": actor_type,
            "actor_attributes": actor_attributes or {},
            "scope": scope,
            "time_nano": time_nano,
        })

        super().__init__(
            event_type=event_type or docker_event_type.value,
            source=source,
            data=event_data,
            metadata=metadata,
            event_id=event_id,
            timestamp=timestamp,
        )

    def _validate(self) -> None:
        """Validate Docker event data."""
        # Call parent validation
        if not self._event_type:
            raise ValueError("event_type cannot be empty")
        
        # Docker-specific validation
        if not self.docker_event_id:
            raise ValueError("docker_event_id cannot be empty")
        if not self.actor_id:
            raise ValueError("actor_id cannot be empty")

    @property
    def is_container_event(self) -> bool:
        """Check if this is a container event."""
        return self.docker_event_type.value.startswith("container.")

    @property
    def is_network_event(self) -> bool:
        """Check if this is a network event."""
        return self.docker_event_type.value.startswith("network.")

    @property
    def is_volume_event(self) -> bool:
        """Check if this is a volume event."""
        return self.docker_event_type.value.startswith("volume.")

    @property
    def is_image_event(self) -> bool:
        """Check if this is an image event."""
        return self.docker_event_type.value.startswith("image.")


class DockerContainerEvent(DockerEvent):
    """Docker container event with container-specific details."""

    def __init__(
        self,
        docker_event_type: DockerEventType,
        source: str,
        docker_event_id: str,
        docker_timestamp: datetime,
        docker_action: str,
        actor_id: str,
        actor_type: str,
        container_id: str,
        container_name: Optional[str] = None,
        container_image: Optional[str] = None,
        container_state: Optional[DockerContainerState] = None,
        target_node_address: Optional[str] = None,
        target_node_port: Optional[int] = None,
        **kwargs
    ):
        """Initialize Docker container event."""
        # Store container attributes BEFORE calling super()
        self.container_id = container_id
        self.container_name = container_name
        self.container_image = container_image
        self.container_state = container_state
        self.target_node_address = target_node_address
        self.target_node_port = target_node_port

        # Add container-specific data
        container_data = {
            "container_id": container_id,
            "container_name": container_name,
            "container_image": container_image,
            "container_state": container_state.value if container_state else None,
            "target_node_address": target_node_address,
            "target_node_port": target_node_port,
        }

        data = kwargs.get("data", {})
        data.update(container_data)
        kwargs["data"] = data

        super().__init__(
            event_type=docker_event_type.value,
            source=source,
            docker_event_id=docker_event_id,
            docker_event_type=docker_event_type,
            docker_timestamp=docker_timestamp,
            docker_action=docker_action,
            actor_id=actor_id,
            actor_type=actor_type,
            **kwargs
        )

    @property
    def short_container_id(self) -> str:
        """Get short container ID (first 12 characters)."""
        return self.container_id[:12] if self.container_id else ""


class DockerNetworkEvent(DockerEvent):
    """Docker network event with network-specific details."""

    def __init__(
        self,
        docker_event_type: DockerEventType,
        source: str,
        docker_event_id: str,
        docker_timestamp: datetime,
        docker_action: str,
        actor_id: str,
        actor_type: str,
        network_id: str,
        network_name: Optional[str] = None,
        network_driver: Optional[str] = None,
        network_scope: Optional[str] = None,
        container_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize Docker network event."""
        network_data = {
            "network_id": network_id,
            "network_name": network_name,
            "network_driver": network_driver,
            "network_scope": network_scope,
            "container_id": container_id,
        }

        data = kwargs.get("data", {})
        data.update(network_data)
        kwargs["data"] = data

        super().__init__(
            event_type=docker_event_type.value,
            source=source,
            docker_event_id=docker_event_id,
            docker_event_type=docker_event_type,
            docker_timestamp=docker_timestamp,
            docker_action=docker_action,
            actor_id=actor_id,
            actor_type=actor_type,
            **kwargs
        )

        self.network_id = network_id
        self.network_name = network_name
        self.network_driver = network_driver
        self.network_scope = network_scope
        self.container_id = container_id


class DockerVolumeEvent(DockerEvent):
    """Docker volume event with volume-specific details."""

    def __init__(
        self,
        docker_event_type: DockerEventType,
        source: str,
        docker_event_id: str,
        docker_timestamp: datetime,
        docker_action: str,
        actor_id: str,
        actor_type: str,
        volume_name: str,
        volume_driver: Optional[str] = None,
        mount_point: Optional[str] = None,
        container_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize Docker volume event."""
        volume_data = {
            "volume_name": volume_name,
            "volume_driver": volume_driver,
            "mount_point": mount_point,
            "container_id": container_id,
        }

        data = kwargs.get("data", {})
        data.update(volume_data)
        kwargs["data"] = data

        super().__init__(
            event_type=docker_event_type.value,
            source=source,
            docker_event_id=docker_event_id,
            docker_event_type=docker_event_type,
            docker_timestamp=docker_timestamp,
            docker_action=docker_action,
            actor_id=actor_id,
            actor_type=actor_type,
            **kwargs
        )

        self.volume_name = volume_name
        self.volume_driver = volume_driver
        self.mount_point = mount_point
        self.container_id = container_id


class DockerImageEvent(DockerEvent):
    """Docker image event with image-specific details."""

    def __init__(
        self,
        docker_event_type: DockerEventType,
        source: str,
        docker_event_id: str,
        docker_timestamp: datetime,
        docker_action: str,
        actor_id: str,
        actor_type: str,
        image_id: str,
        image_name: Optional[str] = None,
        image_tags: Optional[List[str]] = None,
        image_size: Optional[int] = None,
        **kwargs
    ):
        """Initialize Docker image event."""
        image_data = {
            "image_id": image_id,
            "image_name": image_name,
            "image_tags": image_tags or [],
            "image_size": image_size,
        }

        data = kwargs.get("data", {})
        data.update(image_data)
        kwargs["data"] = data

        super().__init__(
            event_type=docker_event_type.value,
            source=source,
            docker_event_id=docker_event_id,
            docker_event_type=docker_event_type,
            docker_timestamp=docker_timestamp,
            docker_action=docker_action,
            actor_id=actor_id,
            actor_type=actor_type,
            **kwargs
        )

        self.image_id = image_id
        self.image_name = image_name
        self.image_tags = image_tags or []
        self.image_size = image_size

    @property
    def short_image_id(self) -> str:
        """Get short image ID (first 12 characters)."""
        return self.image_id[:12] if self.image_id else ""
