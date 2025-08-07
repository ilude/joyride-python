"""Docker event producer for monitoring Docker daemon events."""

import asyncio
import logging
from typing import Any, Dict, Optional, Set

import docker
from docker.errors import DockerException

from app.joyride.events import EventBus
from app.producers.docker_events import (
    DockerContainerEvent,
    DockerEvent,
    DockerEventType,
    DockerImageEvent,
    DockerNetworkEvent,
    DockerVolumeEvent,
)
from app.producers.event_producer import EventProducer

logger = logging.getLogger(__name__)


class DockerEventProducer(EventProducer):
    """Producer for Docker daemon events."""

    def __init__(
        self,
        event_bus: EventBus,
        producer_name: str = "docker_event_producer",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Docker event producer.

        Args:
            event_bus: Event bus to publish events to
            producer_name: Name of this producer instance
            config: Configuration options including:
                - docker_url: Docker daemon URL (default: unix://var/run/docker.sock)
                - api_version: Docker API version (default: auto)
                - timeout: Docker client timeout (default: 60)
                - event_filters: Docker event filters (default: None)
        """
        super().__init__(event_bus, producer_name, config)

        # Docker client configuration
        self._docker_url = config.get("docker_url", "unix://var/run/docker.sock")
        self._api_version = config.get("api_version", "auto")
        self._timeout = config.get("timeout", 60)
        self._event_filters = config.get("event_filters", {})

        # Docker client and event stream
        self._docker_client: Optional[docker.DockerClient] = None
        self._event_stream = None

        # Supported event types
        self._supported_event_types = {
            event_type.value for event_type in DockerEventType
        }

    async def _start_producer(self) -> None:
        """Start the Docker event producer."""
        try:
            # Initialize Docker client
            self._docker_client = docker.DockerClient(
                base_url=self._docker_url,
                version=self._api_version,
                timeout=self._timeout,
            )

            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                None, self._docker_client.ping
            )

            logger.info(f"Connected to Docker daemon at {self._docker_url}")

        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to Docker: {e}")
            raise

    async def _stop_producer(self) -> None:
        """Stop the Docker event producer."""
        if self._event_stream:
            try:
                self._event_stream.close()
            except Exception as e:
                logger.warning(f"Error closing Docker event stream: {e}")
            finally:
                self._event_stream = None

        if self._docker_client:
            try:
                self._docker_client.close()
            except Exception as e:
                logger.warning(f"Error closing Docker client: {e}")
            finally:
                self._docker_client = None

    async def _run_producer(self) -> None:
        """Main producer loop to monitor Docker events."""
        if not self._docker_client:
            logger.error("Docker client not initialized")
            return

        logger.info("Starting Docker event monitoring")

        try:
            # Get event stream from Docker daemon
            self._event_stream = self._docker_client.events(
                filters=self._event_filters, decode=True
            )

            # Process events in executor to avoid blocking
            while self._is_running:
                try:
                    # Get next event with timeout
                    event_data = await asyncio.get_event_loop().run_in_executor(
                        None, self._get_next_event
                    )

                    if event_data:
                        await self._process_docker_event(event_data)

                except asyncio.CancelledError:
                    logger.info("Docker event monitoring cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error processing Docker event: {e}")
                    await asyncio.sleep(1)  # Brief pause before retry

        except Exception as e:
            logger.error(f"Docker event stream error: {e}")
            raise
        finally:
            logger.info("Docker event monitoring stopped")

    def _get_next_event(self) -> Optional[Dict[str, Any]]:
        """Get next event from Docker event stream (blocking)."""
        if not self._event_stream:
            return None

        try:
            return next(self._event_stream)
        except StopIteration:
            return None
        except Exception as e:
            logger.warning(f"Error getting Docker event: {e}")
            return None

    async def _process_docker_event(self, event_data: Dict[str, Any]) -> None:
        """Process a Docker event and create appropriate event object."""
        try:
            event_type = event_data.get("Type", "")
            action = event_data.get("Action", "")

            # Create event type enum value
            docker_event_type = self._map_docker_event_type(event_type, action)
            if not docker_event_type:
                logger.debug(f"Skipping unmapped Docker event: {event_type}.{action}")
                return

            # Create appropriate event object based on event type
            event = await self._create_event_object(docker_event_type, event_data)
            if event:
                await self.publish_event(event)

        except Exception as e:
            logger.error(f"Error processing Docker event: {e}")
            logger.debug(f"Event data: {event_data}")

    def _map_docker_event_type(
        self, event_type: str, action: str
    ) -> Optional[DockerEventType]:
        """Map Docker event type and action to DockerEventType enum."""
        event_mapping = {
            ("container", "start"): DockerEventType.CONTAINER_START,
            ("container", "stop"): DockerEventType.CONTAINER_STOP,
            ("container", "restart"): DockerEventType.CONTAINER_RESTART,
            ("container", "die"): DockerEventType.CONTAINER_DIE,
            ("container", "kill"): DockerEventType.CONTAINER_KILL,
            ("container", "pause"): DockerEventType.CONTAINER_PAUSE,
            ("container", "unpause"): DockerEventType.CONTAINER_UNPAUSE,
            ("container", "create"): DockerEventType.CONTAINER_CREATE,
            ("container", "destroy"): DockerEventType.CONTAINER_DESTROY,
            ("container", "rename"): DockerEventType.CONTAINER_RENAME,
            ("container", "update"): DockerEventType.CONTAINER_UPDATE,
            ("network", "connect"): DockerEventType.NETWORK_CONNECT,
            ("network", "disconnect"): DockerEventType.NETWORK_DISCONNECT,
            ("network", "create"): DockerEventType.NETWORK_CREATE,
            ("network", "destroy"): DockerEventType.NETWORK_DESTROY,
            ("volume", "create"): DockerEventType.VOLUME_CREATE,
            ("volume", "destroy"): DockerEventType.VOLUME_DESTROY,
            ("volume", "mount"): DockerEventType.VOLUME_MOUNT,
            ("volume", "unmount"): DockerEventType.VOLUME_UNMOUNT,
            ("image", "pull"): DockerEventType.IMAGE_PULL,
            ("image", "push"): DockerEventType.IMAGE_PUSH,
            ("image", "delete"): DockerEventType.IMAGE_DELETE,
            ("image", "tag"): DockerEventType.IMAGE_TAG,
            ("image", "untag"): DockerEventType.IMAGE_UNTAG,
        }

        return event_mapping.get((event_type.lower(), action.lower()))

    async def _create_event_object(
        self, docker_event_type: DockerEventType, event_data: Dict[str, Any]
    ) -> Optional[DockerEvent]:
        """Create appropriate event object based on Docker event type."""
        try:
            # Extract common fields
            common_fields = {
                "event_type": docker_event_type.value,
                "source": self._producer_name,
                "docker_event_id": event_data.get("id", ""),
                "docker_event_type": docker_event_type,
                "docker_timestamp": event_data.get("time"),
                "docker_action": event_data.get("Action", ""),
                "actor_id": event_data.get("Actor", {}).get("ID", ""),
                "actor_type": event_data.get("Type", ""),
                "actor_attributes": event_data.get("Actor", {}).get("Attributes", {}),
                "scope": event_data.get("scope"),
                "time_nano": event_data.get("timeNano"),
            }

            # Create specific event type based on Docker event category
            if docker_event_type.value.startswith("container."):
                return await self._create_container_event(common_fields, event_data)
            elif docker_event_type.value.startswith("network."):
                return await self._create_network_event(common_fields, event_data)
            elif docker_event_type.value.startswith("volume."):
                return await self._create_volume_event(common_fields, event_data)
            elif docker_event_type.value.startswith("image."):
                return await self._create_image_event(common_fields, event_data)
            else:
                # Fallback to base DockerEvent
                return DockerEvent(**common_fields)

        except Exception as e:
            logger.error(f"Error creating event object: {e}")
            return None

    async def _create_container_event(
        self, common_fields: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Optional[DockerContainerEvent]:
        """Create container-specific event."""
        try:
            container_id = common_fields["actor_id"]
            attributes = common_fields["actor_attributes"]

            # Extract container information
            container_fields = {
                **common_fields,
                "container_id": container_id,
                "container_name": attributes.get("name", ""),
                "container_image": attributes.get("image", ""),
                "container_labels": {
                    k: v for k, v in attributes.items() if k.startswith("label.")
                },
            }

            # Try to get additional container info from Docker API
            if self._docker_client and container_id:
                try:
                    container_info = await asyncio.get_event_loop().run_in_executor(
                        None, self._get_container_info, container_id
                    )
                    if container_info:
                        container_fields.update(container_info)
                except Exception as e:
                    logger.debug(
                        f"Could not get container info for {container_id}: {e}"
                    )

            return DockerContainerEvent(**container_fields)

        except Exception as e:
            logger.error(f"Error creating container event: {e}")
            return None

    async def _create_network_event(
        self, common_fields: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Optional[DockerNetworkEvent]:
        """Create network-specific event."""
        try:
            network_id = common_fields["actor_id"]
            attributes = common_fields["actor_attributes"]

            network_fields = {
                **common_fields,
                "network_id": network_id,
                "network_name": attributes.get("name", ""),
                "network_driver": attributes.get("driver"),
                "network_scope": attributes.get("scope"),
                "connected_container_id": attributes.get("container"),
                "endpoint_id": attributes.get("endpointID"),
            }

            return DockerNetworkEvent(**network_fields)

        except Exception as e:
            logger.error(f"Error creating network event: {e}")
            return None

    async def _create_volume_event(
        self, common_fields: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Optional[DockerVolumeEvent]:
        """Create volume-specific event."""
        try:
            volume_name = common_fields["actor_id"]
            attributes = common_fields["actor_attributes"]

            volume_fields = {
                **common_fields,
                "volume_name": volume_name,
                "volume_driver": attributes.get("driver"),
                "volume_mountpoint": attributes.get("mountpoint"),
                "mount_container_id": attributes.get("container"),
                "mount_destination": attributes.get("destination"),
                "mount_mode": attributes.get("read/write"),
            }

            return DockerVolumeEvent(**volume_fields)

        except Exception as e:
            logger.error(f"Error creating volume event: {e}")
            return None

    async def _create_image_event(
        self, common_fields: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Optional[DockerImageEvent]:
        """Create image-specific event."""
        try:
            image_id = common_fields["actor_id"]
            attributes = common_fields["actor_attributes"]

            # Parse image name and tag
            image_name = attributes.get("name", "")
            image_tag = None
            if ":" in image_name:
                image_name, image_tag = image_name.rsplit(":", 1)

            image_fields = {
                **common_fields,
                "image_id": image_id,
                "image_name": image_name,
                "image_tag": image_tag,
                "image_digest": attributes.get("digest"),
                "repository": attributes.get("repository"),
            }

            return DockerImageEvent(**image_fields)

        except Exception as e:
            logger.error(f"Error creating image event: {e}")
            return None

    def _get_container_info(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Get additional container information from Docker API."""
        try:
            container = self._docker_client.containers.get(container_id)

            # Extract relevant information
            network_settings = container.attrs.get("NetworkSettings", {})
            config = container.attrs.get("Config", {})

            return {
                "container_state": container.status,
                "hostname": config.get("Hostname"),
                "domainname": config.get("Domainname"),
                "dns_servers": config.get("Dns", []),
                "network_settings": network_settings,
                "port_mappings": network_settings.get("Ports", {}),
            }

        except Exception:
            # Container might not exist anymore
            return None

    def get_supported_event_types(self) -> Set[str]:
        """Get set of supported Docker event types."""
        return self._supported_event_types.copy()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for Docker event producer."""
        health_data = await super().health_check()

        # Add Docker-specific health information
        docker_health = {
            "docker_connection": False,
            "docker_url": self._docker_url,
            "api_version": self._api_version,
            "event_stream_active": self._event_stream is not None,
        }

        if self._docker_client:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._docker_client.ping
                )
                docker_health["docker_connection"] = True
            except Exception as e:
                docker_health["docker_error"] = str(e)

        health_data["docker"] = docker_health
        return health_data
