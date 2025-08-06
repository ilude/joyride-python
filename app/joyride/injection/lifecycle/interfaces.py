"""Minimal protocol interfaces."""

from typing import Protocol

from .types import HealthStatus


class Startable(Protocol):
    """Protocol for startable components."""
    async def start(self) -> None: ...


class Stoppable(Protocol):
    """Protocol for stoppable components."""
    async def stop(self) -> None: ...


class HealthCheckable(Protocol):
    """Protocol for health checkable components."""
    async def health_check(self) -> HealthStatus: ...


class Logger(Protocol):
    """Simple logger protocol."""
    def info(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
    def debug(self, message: str) -> None: ...
