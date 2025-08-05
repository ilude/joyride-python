"""
Event filter for the Joyride DNS Service registry system.

This module provides event filtering capabilities with pattern matching
and custom filter functions.
"""

import fnmatch
import re
from typing import Callable, Optional, Pattern

from .event_base import JoyrideEvent


class JoyrideEventFilter:
    """
    Represents a filter for event subscription in the Joyride DNS Service.

    Supports exact matching, wildcard patterns, and custom filtering functions
    for flexible event routing and subscription management.
    """

    def __init__(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        pattern: Optional[str] = None,
        custom_filter: Optional[Callable[[JoyrideEvent], bool]] = None,
    ):
        """
        Initialize event filter.

        Args:
            event_type: Exact event type to match
            source: Exact source to match
            pattern: Wildcard pattern to match against event_type
            custom_filter: Custom function for complex filtering
        """
        self.event_type = event_type
        self.source = source
        self.pattern = pattern
        self.custom_filter = custom_filter

        # Compile pattern for efficiency
        self._compiled_pattern: Optional[Pattern[str]] = None
        if pattern:
            # Convert shell-style wildcards to regex
            regex_pattern = fnmatch.translate(pattern)
            self._compiled_pattern = re.compile(regex_pattern, re.IGNORECASE)

    def matches(self, event: JoyrideEvent) -> bool:
        """
        Check if an event matches this filter.

        Args:
            event: Event to check

        Returns:
            True if event matches the filter
        """
        # Check exact event type match
        if self.event_type and event.event_type != self.event_type:
            return False

        # Check exact source match
        if self.source and event.source != self.source:
            return False

        # Check pattern match
        if self._compiled_pattern and not self._compiled_pattern.match(
            event.event_type
        ):
            return False

        # Check custom filter
        if self.custom_filter and not self.custom_filter(event):
            return False

        return True

    def __str__(self) -> str:
        """String representation of the filter."""
        parts = []
        if self.event_type:
            parts.append(f"type={self.event_type}")
        if self.source:
            parts.append(f"source={self.source}")
        if self.pattern:
            parts.append(f"pattern={self.pattern}")
        if self.custom_filter:
            parts.append("custom_filter=True")
        return f"JoyrideEventFilter({', '.join(parts)})"
