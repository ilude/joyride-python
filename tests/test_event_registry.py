"""
Tests for the event registry system.

Tests event type r        event = DNSEvent(
            event_type="dns.record.created",
            source="docker_monitor",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1"
        )ration, subscription management, filtering, and pattern matching.
"""

import threading
from unittest.mock import Mock

import pytest

from app.joyride.events import (
    EventFilter,
    EventRegistry,
    EventSubscription,
)
from app.joyride.events.types import ContainerEvent, DNSEvent


class TestEventFilter:
    """Test EventFilter functionality."""

    def test_filter_creation(self):
        """Test basic filter creation."""
        filter_obj = EventFilter(event_type="dns.record.created")
        assert filter_obj.event_type == "dns.record.created"
        assert filter_obj.source is None
        assert filter_obj.pattern is None
        assert filter_obj.custom_filter is None

    def test_exact_event_type_match(self):
        """Test exact event type matching."""
        filter_obj = EventFilter(event_type="dns.record.created")

        # Create test event
        event = DNSEvent(
            event_type="dns.record.created",
            source="test",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )

        assert filter_obj.matches(event) is True

        # Different event type should not match
        event2 = DNSEvent(
            event_type="dns.record.updated",
            source="test",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.2",
        )

        assert filter_obj.matches(event2) is False

    def test_exact_source_match(self):
        """Test exact source matching."""
        filter_obj = EventFilter(source="docker_monitor")

        event = DNSEvent(
            event_type="dns.record.created",
            source="docker_monitor",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )

        assert filter_obj.matches(event) is True

        # Different source should not match
        event2 = DNSEvent(
            event_type="dns.record.created",
            source="hosts_monitor",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )

        assert filter_obj.matches(event2) is False

    def test_pattern_matching(self):
        """Test wildcard pattern matching."""
        filter_obj = EventFilter(pattern="dns.*")

        # Should match dns.record.created
        event1 = DNSEvent(
            event_type="dns.record.created",
            source="test",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )
        assert filter_obj.matches(event1) is True

        # Should match dns.record.deleted
        event2 = DNSEvent(
            event_type="dns.record.deleted",
            source="test",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )
        assert filter_obj.matches(event2) is True

        # Should not match container.started
        event3 = ContainerEvent(
            event_type="container.started",
            source="test",
            container_id="123",
            container_name="test",
            image="nginx",
        )
        assert filter_obj.matches(event3) is False

    def test_complex_pattern_matching(self):
        """Test more complex pattern matching."""
        # Test specific pattern
        filter_obj = EventFilter(pattern="container.start*")

        event1 = ContainerEvent(
            event_type="container.started",
            source="test",
            container_id="123",
            container_name="test",
            image="nginx",
        )
        assert filter_obj.matches(event1) is True

        event2 = ContainerEvent(
            event_type="container.starting",
            source="test",
            container_id="123",
            container_name="test",
            image="nginx",
        )
        assert filter_obj.matches(event2) is True

        event3 = ContainerEvent(
            event_type="container.stopped",
            source="test",
            container_id="123",
            container_name="test",
            image="nginx",
        )
        assert filter_obj.matches(event3) is False

    def test_custom_filter(self):
        """Test custom filter function."""

        def custom_func(event):
            return hasattr(event, "record_name") and event.record_name.endswith(".com")

        filter_obj = EventFilter(custom_filter=custom_func)

        # Should match .com domain
        event1 = DNSEvent(
            event_type="dns.record.created",
            source="test",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )
        assert filter_obj.matches(event1) is True

        # Should not match .org domain
        event2 = DNSEvent(
            event_type="dns.record.created",
            source="test",
            record_name="example.org",
            record_type="A",
            record_value="192.168.1.1",
        )
        assert filter_obj.matches(event2) is False

    def test_combined_filters(self):
        """Test combining multiple filter criteria."""
        filter_obj = EventFilter(pattern="dns.*", source="docker_monitor")

        # Should match both pattern and source
        event1 = DNSEvent(
            event_type="dns.record.created",
            source="docker_monitor",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )
        assert filter_obj.matches(event1) is True

        # Should not match (wrong source)
        event2 = DNSEvent(
            event_type="dns.record.created",
            source="hosts_monitor",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )
        assert filter_obj.matches(event2) is False

        # Should not match (wrong pattern)
        event3 = ContainerEvent(
            event_type="container.started",
            source="docker_monitor",
            container_id="123",
            container_name="test",
            image="nginx",
        )
        assert filter_obj.matches(event3) is False

    def test_filter_string_representation(self):
        """Test filter string representation."""
        filter_obj = EventFilter(
            event_type="dns.record.created", source="test", pattern="dns.*"
        )

        str_repr = str(filter_obj)
        assert "type=dns.record.created" in str_repr
        assert "source=test" in str_repr
        assert "pattern=dns.*" in str_repr


class TestEventSubscription:
    """Test EventSubscription functionality."""

    def test_subscription_creation(self):
        """Test subscription creation."""
        handler = Mock()
        filter_obj = EventFilter(event_type="test.event")

        subscription = EventSubscription(
            handler=handler, event_filter=filter_obj, subscription_id="test_sub_1"
        )

        assert subscription.handler == handler
        assert subscription.event_filter == filter_obj
        assert subscription.subscription_id == "test_sub_1"
        assert subscription.active is True

    def test_subscription_matching(self):
        """Test subscription event matching."""
        handler = Mock()
        filter_obj = EventFilter(event_type="dns.record.created")

        subscription = EventSubscription(
            handler=handler, event_filter=filter_obj, subscription_id="test_sub_1"
        )

        # Matching event
        event1 = DNSEvent(
            event_type="dns.record.created",
            source="test",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )
        assert subscription.matches(event1) is True

        # Non-matching event
        event2 = DNSEvent(
            event_type="dns.record.deleted",
            source="test",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )
        assert subscription.matches(event2) is False

    def test_subscription_handling(self):
        """Test subscription event handling."""
        handler = Mock()
        filter_obj = EventFilter(event_type="dns.record.created")

        subscription = EventSubscription(
            handler=handler, event_filter=filter_obj, subscription_id="test_sub_1"
        )

        event = DNSEvent(
            event_type="dns.record.created",
            source="test",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )

        subscription.handle(event)
        handler.assert_called_once_with(event)

    def test_subscription_deactivation(self):
        """Test subscription deactivation."""
        handler = Mock()
        filter_obj = EventFilter(event_type="dns.record.created")

        subscription = EventSubscription(
            handler=handler, event_filter=filter_obj, subscription_id="test_sub_1"
        )

        event = DNSEvent(
            event_type="dns.record.created",
            source="test",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )

        # Should match when active
        assert subscription.matches(event) is True

        subscription.deactivate()

        # Should not match when deactivated
        assert subscription.matches(event) is False
        assert subscription.active is False

        # Should not call handler when deactivated
        subscription.handle(event)
        handler.assert_not_called()


class TestEventRegistry:
    """Test EventRegistry functionality."""

    def setup_method(self):
        """Set up test registry."""
        self.registry = EventRegistry()

    def test_registry_creation(self):
        """Test registry creation."""
        assert len(self.registry.list_event_types()) == 0
        assert self.registry.get_subscription_count() == 0

    def test_event_type_registration(self):
        """Test event type registration."""
        self.registry.register_event_type(DNSEvent)

        event_types = self.registry.list_event_types()
        assert "DNSEvent" in event_types

        retrieved_type = self.registry.get_event_type("DNSEvent")
        assert retrieved_type == DNSEvent

    def test_duplicate_event_type_registration(self):
        """Test registering the same event type twice."""
        self.registry.register_event_type(DNSEvent)
        # Should not raise error
        self.registry.register_event_type(DNSEvent)

        assert len(self.registry.list_event_types()) == 1

    def test_invalid_event_type_registration(self):
        """Test registering invalid event type."""

        class NotAnEvent:
            pass

        with pytest.raises(ValueError, match="must inherit from Event"):
            self.registry.register_event_type(NotAnEvent)

    def test_subscription_creation(self):
        """Test creating subscriptions."""
        handler = Mock()

        sub_id = self.registry.subscribe(
            handler=handler, event_type="dns.record.created"
        )

        assert sub_id.startswith("sub_")
        assert self.registry.get_subscription_count() == 1

    def test_subscription_validation(self):
        """Test subscription validation."""
        # Invalid handler
        with pytest.raises(ValueError, match="Handler must be callable"):
            self.registry.subscribe(handler="not_callable")

        # No filter criteria
        handler = Mock()
        with pytest.raises(ValueError, match="At least one filter criterion"):
            self.registry.subscribe(handler=handler)

    def test_subscription_unsubscribe(self):
        """Test unsubscribing."""
        handler = Mock()

        sub_id = self.registry.subscribe(
            handler=handler, event_type="dns.record.created"
        )

        assert self.registry.get_subscription_count() == 1

        # Successful unsubscribe
        result = self.registry.unsubscribe(sub_id)
        assert result is True
        assert self.registry.get_subscription_count() == 0

        # Unsubscribe non-existent subscription
        result = self.registry.unsubscribe("nonexistent")
        assert result is False

    def test_matching_subscriptions(self):
        """Test finding matching subscriptions."""
        handler1 = Mock()
        handler2 = Mock()

        # Subscribe to DNS events
        sub1 = self.registry.subscribe(handler=handler1, pattern="dns.*")

        # Subscribe to specific event type
        sub2 = self.registry.subscribe(
            handler=handler2, event_type="dns.record.created"
        )

        event = DNSEvent(
            event_type="dns.record.created",
            source="test",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
        )

        matching = self.registry.get_matching_subscriptions(event)
        assert len(matching) == 2

        # Both subscriptions should match
        subscription_ids = [sub.subscription_id for sub in matching]
        assert sub1 in subscription_ids
        assert sub2 in subscription_ids

    def test_subscription_info(self):
        """Test getting subscription information."""
        handler = Mock()
        handler.__name__ = "test_handler"

        sub_id = self.registry.subscribe(
            handler=handler, event_type="dns.record.created"
        )

        info = self.registry.get_subscription_info(sub_id)

        assert info is not None
        assert info["subscription_id"] == sub_id
        assert info["active"] is True
        assert "test_handler" in info["handler"]
        assert "type=dns.record.created" in info["filter"]

        # Non-existent subscription
        info = self.registry.get_subscription_info("nonexistent")
        assert info is None

    def test_clear_subscriptions(self):
        """Test clearing all subscriptions."""
        handler = Mock()

        self.registry.subscribe(handler=handler, event_type="test1")
        self.registry.subscribe(handler=handler, event_type="test2")

        assert self.registry.get_subscription_count() == 2

        self.registry.clear_subscriptions()
        assert self.registry.get_subscription_count() == 0

    def test_thread_safety(self):
        """Test thread safety of registry operations."""
        handler = Mock()
        subscription_ids = []

        def subscribe_worker():
            for i in range(10):
                sub_id = self.registry.subscribe(
                    handler=handler, event_type=f"test.event.{i}"
                )
                subscription_ids.append(sub_id)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=subscribe_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have 50 subscriptions (5 threads × 10 subscriptions each)
        assert self.registry.get_subscription_count() == 50
        assert len(subscription_ids) == 50
        assert len(set(subscription_ids)) == 50  # All unique


if __name__ == "__main__":
    pytest.main([__file__])
