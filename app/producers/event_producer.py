"""
Event producer base class and interfaces.

This module provides the abstract base class and common functionality
for all event producers in the Joyride DNS Service.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from app.joyride.events.event import Event
from app.joyride.events.event_bus import EventBus
from app.joyride.injection.lifecycle.component import StartableComponent

logger = logging.getLogger(__name__)


class EventProducer(StartableComponent, ABC):
    """
    Abstract base class for all event producers.

    Event producers are responsible for generating events from various sources
    and publishing them to the event bus. They integrate with the lifecycle
    management system and provide common functionality like error handling,
    retry logic, and metrics collection.
    """

    def __init__(
        self,
        event_bus: EventBus,
        producer_name: str,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the event producer.

        Args:
            event_bus: The event bus to publish events to
            producer_name: Unique name for this producer instance
            config: Optional configuration dictionary
        """
        super().__init__(name=producer_name)
        self._event_bus = event_bus
        self._producer_name = producer_name
        self._config = config or {}
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._event_count = 0
        self._error_count = 0
        self._last_event_time: Optional[datetime] = None
        self._supported_event_types: Set[str] = set()

    @property
    def producer_name(self) -> str:
        """Get the producer name."""
        return self._producer_name

    @property
    def event_count(self) -> int:
        """Get the number of events produced."""
        return self._event_count

    @property
    def error_count(self) -> int:
        """Get the number of errors encountered."""
        return self._error_count

    @property
    def last_event_time(self) -> Optional[datetime]:
        """Get the timestamp of the last event produced."""
        return self._last_event_time

    @property
    def supported_event_types(self) -> Set[str]:
        """Get the set of event types this producer can generate."""
        return self._supported_event_types.copy()

    @property
    def is_running(self) -> bool:
        """Check if the producer is currently running."""
        return self._is_running

    def publish_event(self, event: Event) -> None:
        """
        Publish an event to the event bus with error handling.

        Args:
            event: The event to publish

        Raises:
            RuntimeError: If the producer is not running
        """
        if not self._is_running:
            raise RuntimeError(f"Producer {self._producer_name} is not running")

        try:
            # Add producer metadata
            if hasattr(event, "metadata") and event.metadata is not None:
                event.metadata["producer"] = self._producer_name

            self._event_bus.publish(event)
            self._event_count += 1
            self._last_event_time = datetime.now(timezone.utc)

            logger.debug(
                f"Producer {self._producer_name} published event: "
                f"{event.event_type} from {event.source}"
            )

        except Exception as e:
            self._error_count += 1
            logger.error(
                f"Producer {self._producer_name} failed to publish event: "
                f"{event.event_type} - {e}"
            )
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get producer metrics and statistics.

        Returns:
            Dictionary containing producer metrics
        """
        return {
            "producer_name": self._producer_name,
            "is_running": self._is_running,
            "event_count": self._event_count,
            "error_count": self._error_count,
            "last_event_time": self._last_event_time.isoformat()
            if self._last_event_time
            else None,
            "supported_event_types": list(self._supported_event_types),
            "config": self._config,
        }

    async def start(self) -> None:
        """Start the event producer."""
        if self._is_running:
            logger.warning(f"Producer {self._producer_name} is already running")
            return

        try:
            logger.info(f"Starting event producer: {self._producer_name}")
            await self._start_producer()
            self._is_running = True

            # Start the producer task if it requires async execution
            if hasattr(self, "_run_producer") and asyncio.iscoroutinefunction(
                getattr(self, "_run_producer", None)
            ):
                self._task = asyncio.create_task(getattr(self, "_run_producer")())

            logger.info(f"Event producer {self._producer_name} started successfully")

        except Exception as e:
            logger.error(f"Failed to start producer {self._producer_name}: {e}")
            self._is_running = False
            raise

    async def stop(self) -> None:
        """Stop the event producer."""
        if not self._is_running:
            logger.warning(f"Producer {self._producer_name} is not running")
            return

        try:
            logger.info(f"Stopping event producer: {self._producer_name}")

            # Cancel the producer task if it exists
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

            await self._stop_producer()
            self._is_running = False

            logger.info(f"Event producer {self._producer_name} stopped successfully")

        except Exception as e:
            logger.error(f"Failed to stop producer {self._producer_name}: {e}")
            raise

    @abstractmethod
    async def _start_producer(self) -> None:
        """
        Start the producer-specific logic.

        This method should be implemented by concrete producer classes
        to initialize their specific event sources and begin monitoring.
        """
        pass

    @abstractmethod
    async def _stop_producer(self) -> None:
        """
        Stop the producer-specific logic.

        This method should be implemented by concrete producer classes
        to clean up resources and stop monitoring.
        """
        pass

    def _register_event_type(self, event_type: str) -> None:
        """
        Register an event type that this producer can generate.

        Args:
            event_type: The event type to register
        """
        self._supported_event_types.add(event_type)

    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value with optional default.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    async def health_check(self) -> dict[str, Any]:
        """
        Perform a health check on the producer.

        Returns:
            Dictionary with health status and details
        """
        health = {"healthy": True}
        try:
            # Basic health check - ensure producer is running
            if not self._is_running:
                health["healthy"] = False

            # Check if too many errors have occurred
            if self._event_count > 0:
                error_rate = self._error_count / self._event_count
                if error_rate > 0.5:  # More than 50% error rate
                    logger.warning(
                        f"Producer {self._producer_name} has high error rate: "
                        f"{error_rate:.2%}"
                    )
                    health["healthy"] = False

            # Allow subclasses to add their own health checks
            health["producer_health"] = await self._producer_health_check()
        except Exception as e:
            logger.error(f"Health check failed for producer {self._producer_name}: {e}")
            health["healthy"] = False
            health["error"] = str(e)
        return health

    async def _producer_health_check(self) -> bool:
        """
        Producer-specific health check.

        Override this method in concrete producers to add specific health checks.

        Returns:
            True if the producer is healthy, False otherwise
        """
        return True
