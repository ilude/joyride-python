"""Event producers for Joyride DNS Service.

This module contains event producers that monitor various system components
and generate events for the event bus system.
"""

from app.producers.docker_producer import DockerEventProducer
from app.producers.event_producer import EventProducer
from app.producers.hosts_producer import HostsFileEventProducer
from app.producers.swim_producer import SWIMEventProducer
from app.producers.system_producer import SystemEventProducer

__all__ = [
    "EventProducer",
    "DockerEventProducer",
    "SWIMEventProducer",
    "HostsFileEventProducer",
    "SystemEventProducer",
]
