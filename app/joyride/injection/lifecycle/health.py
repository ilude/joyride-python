"""Health monitoring for components."""

import asyncio
from typing import Dict, List, Optional

from .interfaces import Logger
from .registry import ComponentRegistry
from .types import HealthStatus


class HealthMonitor:
    """Monitors component health."""
    
    def __init__(
        self,
        registry: ComponentRegistry,
        check_interval: float = 30.0,
        logger: Optional[Logger] = None
    ):
        self._registry = registry
        self._check_interval = check_interval
        self._logger = logger
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    async def start_monitoring(self) -> None:
        """Start periodic health monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            return
        
        self._shutdown_event.clear()
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        
        if self._logger:
            self._logger.info("Started health monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self._shutdown_event.set()
        
        if self._monitoring_task and not self._monitoring_task.done():
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
        
        if self._logger:
            self._logger.info("Stopped health monitoring")
    
    async def check_all(self) -> Dict[str, HealthStatus]:
        """Check health of all components."""
        results = {}
        components = await self._registry.list_components()
        
        for component in components:
            try:
                if hasattr(component, 'health_check'):
                    health_result = await component.health_check()
                    # Convert bool to HealthStatus if needed
                    if isinstance(health_result, bool):
                        results[component.name] = HealthStatus.HEALTHY if health_result else HealthStatus.UNHEALTHY
                    else:
                        results[component.name] = health_result
                else:
                    results[component.name] = HealthStatus.UNKNOWN
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Health check failed for {component.name}: {e}")
                results[component.name] = HealthStatus.UNHEALTHY
        
        return results
    
    async def check_component(self, name: str) -> HealthStatus:
        """Check health of specific component."""
        component = await self._registry.get(name)
        
        try:
            if hasattr(component, 'health_check'):
                health_result = await component.health_check()
                # Convert bool to HealthStatus if needed
                if isinstance(health_result, bool):
                    return HealthStatus.HEALTHY if health_result else HealthStatus.UNHEALTHY
                else:
                    return health_result
            else:
                return HealthStatus.UNKNOWN
        except Exception as e:
            if self._logger:
                self._logger.warning(f"Health check failed for {name}: {e}")
            return HealthStatus.UNHEALTHY
    
    async def get_unhealthy_components(self) -> List[str]:
        """Get list of unhealthy component names."""
        health_results = await self.check_all()
        return [
            name for name, status in health_results.items()
            if status == HealthStatus.UNHEALTHY
        ]
    
    async def _monitor_loop(self) -> None:
        """Periodic health monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(), timeout=self._check_interval
                )
                break  # Shutdown requested
            except asyncio.TimeoutError:
                pass  # Timeout reached, do health check
            
            try:
                unhealthy = await self.get_unhealthy_components()
                if unhealthy and self._logger:
                    self._logger.warning(f"Unhealthy components: {unhealthy}")
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Health monitoring error: {e}")
