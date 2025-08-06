"""Lifecycle orchestrator for startup/shutdown coordination."""

from typing import List, Optional

from .component import Component
from .interfaces import Logger
from .registry import ComponentRegistry
from .types import LifecycleError


class LifecycleOrchestrator:
    """Orchestrates component startup and shutdown."""

    def __init__(self, registry: ComponentRegistry, logger: Optional[Logger] = None):
        self._registry = registry
        self._logger = logger

    async def start_all(self) -> None:
        """Start all components in dependency order."""
        startup_order = await self._get_startup_order()

        if self._logger:
            self._logger.info(f"Starting components: {startup_order}")

        for name in startup_order:
            component = await self._registry.get(name)
            if hasattr(component, "start") and (
                component.is_stopped() or component.is_created()
            ):
                await component.start()

    async def stop_all(self) -> None:
        """Stop all components in reverse dependency order."""
        shutdown_order = await self._get_shutdown_order()

        if self._logger:
            self._logger.info(f"Stopping components: {shutdown_order}")

        errors = []
        for name in shutdown_order:
            try:
                component = await self._registry.get(name)
                if hasattr(component, "stop") and (
                    component.is_started() or component.is_failed()
                ):
                    await component.stop()
            except Exception as e:
                error_msg = f"Failed to stop {name}: {e}"
                if self._logger:
                    self._logger.error(error_msg)
                errors.append(error_msg)

        if errors:
            raise LifecycleError(f"Some components failed to stop: {'; '.join(errors)}")

    async def start_component(self, name: str) -> None:
        """Start a specific component and its dependencies."""
        startup_order = await self._get_startup_order()

        # Find components that need to be started
        try:
            target_index = startup_order.index(name)
            components_to_start = startup_order[: target_index + 1]
        except ValueError:
            raise LifecycleError(f"Component {name} not found in startup order")

        for comp_name in components_to_start:
            component = await self._registry.get(comp_name)
            if hasattr(component, "start") and (
                component.is_stopped() or component.is_created()
            ):
                await component.start()

    async def stop_component(self, name: str) -> None:
        """Stop a specific component and its dependents."""
        shutdown_order = await self._get_shutdown_order()

        # Find components that need to be stopped
        try:
            target_index = shutdown_order.index(name)
            components_to_stop = shutdown_order[: target_index + 1]
        except ValueError:
            raise LifecycleError(f"Component {name} not found in shutdown order")

        for comp_name in components_to_stop:
            component = await self._registry.get(comp_name)
            if hasattr(component, "stop") and (
                component.is_started() or component.is_failed()
            ):
                await component.stop()

    async def _get_startup_order(self) -> List[str]:
        """Get component startup order using topological sort."""
        components = await self._registry.list_components()

        # Simple topological sort
        visited = set()
        temp_visited = set()
        order = []

        def visit(component: Component):
            if component.name in temp_visited:
                raise LifecycleError(f"Circular dependency detected: {component.name}")
            if component.name in visited:
                return

            temp_visited.add(component.name)

            # Visit dependencies first
            for dep_name in component.get_dependencies():
                # Find dependency component
                for dep_comp in components:
                    if dep_comp.name == dep_name:
                        visit(dep_comp)
                        break

            temp_visited.remove(component.name)
            visited.add(component.name)
            order.append(component.name)

        # Visit all components
        for component in components:
            if component.name not in visited:
                visit(component)

        return order

    async def _get_shutdown_order(self) -> List[str]:
        """Get component shutdown order (reverse of startup)."""
        startup_order = await self._get_startup_order()
        return list(reversed(startup_order))
