"""System event producer for monitoring system health and resources."""

import asyncio
import logging
import platform
from typing import Any, Dict, Optional, Set

import psutil

from app.joyride.events import EventBus
from app.producers.event_producer import EventProducer
from app.producers.system_events import (
    SystemEvent,
    SystemEventType,
    SystemHealthEvent,
    SystemNetworkEvent,
    SystemProcessEvent,
    SystemResourceEvent,
)

logger = logging.getLogger(__name__)


class SystemEventProducer(EventProducer):
    """Producer for system events."""

    def __init__(
        self,
        event_bus: EventBus,
        producer_name: str = "system_event_producer",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize system event producer.

        Args:
            event_bus: Event bus to publish events to
            producer_name: Name of this producer instance
            config: Configuration options including:
                - monitoring_interval: Monitoring interval in seconds (default: 30)
                - cpu_threshold: CPU usage threshold percentage (default: 80)
                - memory_threshold: Memory usage threshold percentage (default: 80)
                - disk_threshold: Disk usage threshold percentage (default: 85)
                - monitor_processes: Monitor process events (default: False)
                - monitor_network: Monitor network events (default: True)
                - monitor_services: Monitor service events (default: False)
        """
        if config is None:
            config = {}
        super().__init__(event_bus, producer_name, config)

        # Configuration
        self._monitoring_interval = config.get("monitoring_interval", 30)
        self._cpu_threshold = config.get("cpu_threshold", 80)
        self._memory_threshold = config.get("memory_threshold", 80)
        self._disk_threshold = config.get("disk_threshold", 85)
        self._monitor_processes_enabled = config.get("monitor_processes", False)
        self._monitor_network = config.get("monitor_network", True)
        self._monitor_services = config.get("monitor_services", False)

        # System information
        self._hostname = platform.node()
        self._system_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

        # State tracking
        self._last_resource_states = {}
        self._last_network_states = {}
        self._alert_counts = {}

        # Supported event types
        self._supported_event_types = {
            event_type.value for event_type in SystemEventType
        }

    async def _start_producer(self) -> None:
        """Start the system event producer."""
        logger.info(f"Starting system monitoring for host: {self._hostname}")

        # Initialize baseline states
        await self._initialize_baseline_states()

        # Publish system startup event
        await self._publish_system_startup_event()

    async def _stop_producer(self) -> None:
        """Stop the system event producer."""
        logger.info("Stopping system event producer")

        # Publish system shutdown event
        await self._publish_system_shutdown_event()

    async def _run_producer(self) -> None:
        """Main producer loop for system monitoring."""
        logger.info("Starting system monitoring loop")

        while self._is_running:
            try:
                # Monitor system resources
                await self._monitor_system_resources()

                # Monitor network interfaces
                if self._monitor_network:
                    await self._monitor_network_interfaces()

                # Monitor processes
                if self._monitor_processes_enabled:
                    await self._monitor_processes()

                # Perform health checks
                await self._perform_health_checks()

                # Wait for next monitoring cycle
                await asyncio.sleep(self._monitoring_interval)

            except asyncio.CancelledError:
                logger.info("System monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(10)  # Brief pause before retry

    async def _initialize_baseline_states(self) -> None:
        """Initialize baseline system states."""
        try:
            # CPU and memory
            self._last_resource_states = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
            }

            # Network interfaces
            if self._monitor_network:
                net_if_addrs = psutil.net_if_addrs()
                net_if_stats = psutil.net_if_stats()

                for interface in net_if_addrs:
                    if interface in net_if_stats:
                        self._last_network_states[interface] = {
                            "is_up": net_if_stats[interface].isup,
                            "addresses": [
                                addr.address for addr in net_if_addrs[interface]
                            ],
                        }

            logger.info("Baseline system states initialized")

        except Exception as e:
            logger.error(f"Error initializing baseline states: {e}")

    async def _monitor_system_resources(self) -> None:
        """Monitor system resource usage."""
        try:
            # Get current resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Check CPU usage
            if cpu_percent > self._cpu_threshold:
                await self._publish_resource_event(
                    "cpu", cpu_percent, self._cpu_threshold, "percent"
                )

            # Check memory usage
            if memory.percent > self._memory_threshold:
                await self._publish_resource_event(
                    "memory", memory.percent, self._memory_threshold, "percent"
                )

            # Check disk usage
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > self._disk_threshold:
                await self._publish_resource_event(
                    "disk", disk_percent, self._disk_threshold, "percent"
                )

            # Update last states
            self._last_resource_states.update(
                {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk_percent,
                }
            )

        except Exception as e:
            logger.error(f"Error monitoring system resources: {e}")

    async def _monitor_network_interfaces(self) -> None:
        """Monitor network interface states."""
        try:
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()

            for interface in net_if_addrs:
                if interface not in net_if_stats:
                    continue

                current_state = net_if_stats[interface]
                current_addrs = [addr.address for addr in net_if_addrs[interface]]

                last_state = self._last_network_states.get(interface, {})
                was_up = last_state.get("is_up", False)

                # Check for interface state changes
                if current_state.isup != was_up:
                    event_type = (
                        SystemEventType.NETWORK_INTERFACE_UP
                        if current_state.isup
                        else SystemEventType.NETWORK_INTERFACE_DOWN
                    )

                    await self._publish_network_event(
                        interface, event_type, current_state, current_addrs
                    )

                # Update last state
                self._last_network_states[interface] = {
                    "is_up": current_state.isup,
                    "addresses": current_addrs,
                }

        except Exception as e:
            logger.error(f"Error monitoring network interfaces: {e}")

    async def _monitor_processes(self) -> None:
        """Monitor process events (basic implementation)."""
        try:
            # This is a simplified implementation
            # In a full implementation, we would track process creation/termination
            for proc in psutil.process_iter(["pid", "name", "status", "cpu_percent"]):
                try:
                    if proc.info["status"] == psutil.STATUS_ZOMBIE:
                        await self._publish_process_event(
                            proc, SystemEventType.PROCESS_CRASHED
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logger.error(f"Error monitoring processes: {e}")

    async def _perform_health_checks(self) -> None:
        """Perform system health checks."""
        try:
            # Basic health check based on resource usage
            cpu_percent = self._last_resource_states.get("cpu_percent", 0)
            memory_percent = self._last_resource_states.get("memory_percent", 0)
            disk_percent = self._last_resource_states.get("disk_percent", 0)

            # Calculate overall health score
            health_score = 1.0
            if cpu_percent > 80:
                health_score -= 0.3
            if memory_percent > 80:
                health_score -= 0.3
            if disk_percent > 85:
                health_score -= 0.4

            health_score = max(0.0, health_score)

            # Determine health status
            if health_score >= 0.8:
                status = "healthy"
            elif health_score >= 0.5:
                status = "warning"
            else:
                status = "unhealthy"

            # Publish health event
            await self._publish_health_event(status, health_score)

        except Exception as e:
            logger.error(f"Error performing health checks: {e}")

    async def _publish_system_startup_event(self) -> None:
        """Publish system startup event."""
        event = SystemEvent(
            event_type=SystemEventType.SYSTEM_STARTUP.value,
            system_event_type=SystemEventType.SYSTEM_STARTUP,
            source=self._producer_name,
            hostname=self._hostname,
            system_info=self._system_info,
        )

        self.publish_event(event)

    async def _publish_system_shutdown_event(self) -> None:
        """Publish system shutdown event."""
        event = SystemEvent(
            event_type=SystemEventType.SYSTEM_SHUTDOWN.value,
            system_event_type=SystemEventType.SYSTEM_SHUTDOWN,
            source=self._producer_name,
            hostname=self._hostname,
            system_info=self._system_info,
        )

        self.publish_event(event)

    async def _publish_resource_event(
        self, resource_type: str, current_value: float, threshold: float, unit: str
    ) -> None:
        """Publish resource threshold event."""
        # Prevent spam by tracking alert counts
        alert_key = f"{resource_type}_alert"
        alert_count = self._alert_counts.get(alert_key, 0)

        # Only publish every 5th alert to prevent spam
        if alert_count % 5 == 0:
            event_type_map = {
                "cpu": SystemEventType.CPU_HIGH_USAGE,
                "memory": SystemEventType.MEMORY_PRESSURE,
                "disk": SystemEventType.DISK_SPACE_LOW,
            }

            event_type = event_type_map.get(resource_type, SystemEventType.CPU_HIGH_USAGE)
            event = SystemResourceEvent(
                event_type=event_type.value,
                system_event_type=event_type,
                source=self._producer_name,
                hostname=self._hostname,
                system_info=self._system_info,
                resource_type=resource_type,
                current_value=current_value,
                threshold_value=threshold,
                unit=unit,
                trend_direction="up" if current_value > threshold else "stable",
            )

            self.publish_event(event)

        self._alert_counts[alert_key] = alert_count + 1

    async def _publish_network_event(
        self, interface: str, event_type: SystemEventType, stats: Any, addresses: list
    ) -> None:
        """Publish network interface event."""
        event = SystemNetworkEvent(
            event_type=event_type.value,
            system_event_type=event_type,
            source=self._producer_name,
            hostname=self._hostname,
            system_info=self._system_info,
            interface_name=interface,
            interface_state="up" if stats.isup else "down",
            ip_addresses=addresses,
            link_speed=getattr(stats, "speed", None),
        )

        self.publish_event(event)

    async def _publish_process_event(
        self, process: Any, event_type: SystemEventType
    ) -> None:
        """Publish process event."""
        try:
            event = SystemProcessEvent(
                event_type=event_type.value,
                system_event_type=event_type,
                source=self._producer_name,
                hostname=self._hostname,
                system_info=self._system_info,
                process_name=process.info.get("name", "unknown"),
                process_id=process.info.get("pid", 0),
                process_state=process.info.get("status", "unknown"),
            )

            self.publish_event(event)

        except Exception as e:
            logger.error(f"Error publishing process event: {e}")

    async def _publish_health_event(self, status: str, score: float) -> None:
        """Publish health check event."""
        event_type = (
            SystemEventType.HEALTH_CHECK_PASSED
            if status == "healthy"
            else SystemEventType.HEALTH_CHECK_FAILED
        )

        event = SystemHealthEvent(
            event_type=event_type.value,
            system_event_type=event_type,
            source=self._producer_name,
            hostname=self._hostname,
            system_info=self._system_info,
            health_check_name="system_overall",
            health_status=status,
            health_score=score,
            component_statuses={
                "cpu": "healthy"
                if self._last_resource_states.get("cpu_percent", 0) < 80
                else "warning",
                "memory": "healthy"
                if self._last_resource_states.get("memory_percent", 0) < 80
                else "warning",
                "disk": "healthy"
                if self._last_resource_states.get("disk_percent", 0) < 85
                else "warning",
            },
        )

        self.publish_event(event)

    def get_supported_event_types(self) -> Set[str]:
        """Get set of supported system event types."""
        return self._supported_event_types.copy()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for system event producer."""
        health_data = await super().health_check()

        # Add system-specific health information
        try:
            system_health = {
                "hostname": self._hostname,
                "monitoring_interval": self._monitoring_interval,
                "cpu_threshold": self._cpu_threshold,
                "memory_threshold": self._memory_threshold,
                "disk_threshold": self._disk_threshold,
                "monitor_processes": self._monitor_processes_enabled,
                "monitor_network": self._monitor_network,
                "monitor_services": self._monitor_services,
                "current_resources": {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": (
                        psutil.disk_usage("/").used / psutil.disk_usage("/").total
                    )
                    * 100,
                },
                "system_info": self._system_info,
            }

            health_data["system"] = system_health

        except Exception as e:
            health_data["system_error"] = str(e)

        return health_data
