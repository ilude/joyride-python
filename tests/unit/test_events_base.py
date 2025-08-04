"""
Unit tests for event system base classes and interfaces.

Tests the foundational abstractions of the event system including Event,
EventProducer, and EventHandler abstract base classes.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.events.base import Event, EventHandler, EventProducer


class ConcreteEvent(Event):
    """Concrete implementation of Event for testing."""
    
    def _validate(self) -> None:
        """Test validation implementation."""
        super()._validate()
        # Add some test-specific validation
        if self.event_type == "invalid":
            raise ValueError("Invalid event type for testing")


class ConcreteEventProducer(EventProducer):
    """Concrete implementation of EventProducer for testing."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.start_called = False
        self.stop_called = False
    
    async def start(self) -> None:
        """Test start implementation."""
        self.start_called = True
        self._running = True
    
    async def stop(self) -> None:
        """Test stop implementation."""
        self.stop_called = True
        self._running = False


class ConcreteEventHandler(EventHandler):
    """Concrete implementation of EventHandler for testing."""
    
    def __init__(self, name: str, handles_types: list = None):
        super().__init__(name)
        self.handles_types = handles_types or ["test"]
        self.handled_events = []
    
    def can_handle(self, event: Event) -> bool:
        """Test can_handle implementation."""
        return event.event_type in self.handles_types
    
    async def handle(self, event: Event) -> None:
        """Test handle implementation."""
        self.handled_events.append(event)


class TestEvent:
    """Test cases for Event abstract base class."""
    
    def test_event_creation_with_defaults(self):
        """Test creating event with default values."""
        event = ConcreteEvent("test.event", "test.source")
        
        assert event.event_type == "test.event"
        assert event.source == "test.source"
        assert isinstance(event.event_id, str)
        assert len(event.event_id) > 0
        assert isinstance(event.timestamp, datetime)
        assert event.data == {}
        assert event.metadata == {}
    
    def test_event_creation_with_custom_values(self):
        """Test creating event with custom values."""
        custom_timestamp = datetime(2024, 1, 1, 12, 0, 0)
        custom_data = {"key": "value"}
        custom_metadata = {"source_version": "1.0"}
        custom_id = "custom-event-id"
        
        event = ConcreteEvent(
            "custom.event",
            "custom.source",
            data=custom_data,
            metadata=custom_metadata,
            event_id=custom_id,
            timestamp=custom_timestamp
        )
        
        assert event.event_id == custom_id
        assert event.event_type == "custom.event"
        assert event.source == "custom.source"
        assert event.timestamp == custom_timestamp
        assert event.data == custom_data
        assert event.metadata == custom_metadata
    
    def test_event_data_immutability(self):
        """Test that event data cannot be modified after creation."""
        original_data = {"key": "value"}
        event = ConcreteEvent("test.event", "test.source", data=original_data)
        
        # Get data returns a copy
        data_copy = event.data
        data_copy["new_key"] = "new_value"
        
        # Original event data should be unchanged
        assert event.data == original_data
        assert "new_key" not in event.data
    
    def test_event_metadata_immutability(self):
        """Test that event metadata cannot be modified after creation."""
        original_metadata = {"version": "1.0"}
        event = ConcreteEvent("test.event", "test.source", metadata=original_metadata)
        
        # Get metadata returns a copy
        metadata_copy = event.metadata
        metadata_copy["new_key"] = "new_value"
        
        # Original event metadata should be unchanged
        assert event.metadata == original_metadata
        assert "new_key" not in event.metadata
    
    def test_get_data_method(self):
        """Test getting data values with defaults."""
        data = {"existing_key": "value"}
        event = ConcreteEvent("test.event", "test.source", data=data)
        
        assert event.get_data("existing_key") == "value"
        assert event.get_data("missing_key") is None
        assert event.get_data("missing_key", "default") == "default"
    
    def test_get_metadata_method(self):
        """Test getting metadata values with defaults."""
        metadata = {"version": "1.0"}
        event = ConcreteEvent("test.event", "test.source", metadata=metadata)
        
        assert event.get_metadata("version") == "1.0"
        assert event.get_metadata("missing_key") is None
        assert event.get_metadata("missing_key", "default") == "default"
    
    def test_event_validation_empty_event_type(self):
        """Test validation fails for empty event type."""
        with pytest.raises(ValueError, match="event_type cannot be empty"):
            ConcreteEvent("", "test.source")
    
    def test_event_validation_empty_source(self):
        """Test validation fails for empty source."""
        with pytest.raises(ValueError, match="source cannot be empty"):
            ConcreteEvent("test.event", "")
    
    def test_event_custom_validation(self):
        """Test custom validation in concrete event class."""
        with pytest.raises(ValueError, match="Invalid event type for testing"):
            ConcreteEvent("invalid", "test.source")
    
    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        data = {"key": "value"}
        metadata = {"version": "1.0"}
        
        event = ConcreteEvent(
            "test.event",
            "test.source",
            data=data,
            metadata=metadata,
            event_id="test-id",
            timestamp=timestamp
        )
        
        result = event.to_dict()
        
        assert result["event_id"] == "test-id"
        assert result["event_type"] == "test.event"
        assert result["source"] == "test.source"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["data"] == data
        assert result["metadata"] == metadata
    
    def test_event_string_representation(self):
        """Test string representation of event."""
        event = ConcreteEvent("test.event", "test.source", event_id="test-id")
        
        str_repr = str(event)
        assert "test.event" in str_repr
        assert "test-id" in str_repr
        assert "test.source" in str_repr
    
    def test_event_repr(self):
        """Test developer representation of event."""
        event = ConcreteEvent("test.event", "test.source", event_id="test-id")
        
        repr_str = repr(event)
        assert "ConcreteEvent" in repr_str
        assert "test-id" in repr_str
        assert "test.event" in repr_str
        assert "test.source" in repr_str


class TestEventProducer:
    """Test cases for EventProducer abstract base class."""
    
    def test_producer_creation(self):
        """Test creating event producer."""
        producer = ConcreteEventProducer("test.producer")
        
        assert producer.name == "test.producer"
        assert not producer.is_running
        assert producer.event_bus is None
    
    def test_set_event_bus(self):
        """Test setting event bus."""
        producer = ConcreteEventProducer("test.producer")
        mock_bus = MagicMock()
        
        producer.set_event_bus(mock_bus)
        
        assert producer.event_bus == mock_bus
    
    @pytest.mark.asyncio
    async def test_producer_lifecycle(self):
        """Test producer start/stop lifecycle."""
        producer = ConcreteEventProducer("test.producer")
        
        assert not producer.is_running
        
        await producer.start()
        assert producer.is_running
        assert producer.start_called
        
        await producer.stop()
        assert not producer.is_running
        assert producer.stop_called
    
    def test_publish_event_success(self):
        """Test successful event publishing."""
        producer = ConcreteEventProducer("test.producer")
        mock_bus = MagicMock()
        producer.set_event_bus(mock_bus)
        
        event = ConcreteEvent("test.event", "test.source")
        producer.publish(event)
        
        mock_bus.publish.assert_called_once_with(event)
    
    def test_publish_event_no_bus(self):
        """Test publishing event without event bus configured."""
        producer = ConcreteEventProducer("test.producer")
        event = ConcreteEvent("test.event", "test.source")
        
        with pytest.raises(RuntimeError, match="No event bus configured"):
            producer.publish(event)
    
    def test_publish_invalid_event(self):
        """Test publishing invalid event."""
        producer = ConcreteEventProducer("test.producer")
        mock_bus = MagicMock()
        producer.set_event_bus(mock_bus)
        
        with pytest.raises(ValueError, match="event must be an instance of Event"):
            producer.publish("not an event")
    
    def test_producer_string_representation(self):
        """Test string representation of producer."""
        producer = ConcreteEventProducer("test.producer")
        
        str_repr = str(producer)
        assert "ConcreteEventProducer" in str_repr
        assert "test.producer" in str_repr
        assert "stopped" in str_repr


class TestEventHandler:
    """Test cases for EventHandler abstract base class."""
    
    def test_handler_creation(self):
        """Test creating event handler."""
        handler = ConcreteEventHandler("test.handler")
        
        assert handler.name == "test.handler"
        assert handler.enabled
    
    def test_handler_enable_disable(self):
        """Test enabling and disabling handler."""
        handler = ConcreteEventHandler("test.handler")
        
        assert handler.enabled
        
        handler.disable()
        assert not handler.enabled
        
        handler.enable()
        assert handler.enabled
    
    def test_can_handle_event(self):
        """Test event filtering with can_handle method."""
        handler = ConcreteEventHandler("test.handler", handles_types=["test", "other"])
        
        test_event = ConcreteEvent("test", "test.source")
        other_event = ConcreteEvent("other", "test.source")
        unknown_event = ConcreteEvent("unknown", "test.source")
        
        assert handler.can_handle(test_event)
        assert handler.can_handle(other_event)
        assert not handler.can_handle(unknown_event)
    
    @pytest.mark.asyncio
    async def test_handle_event(self):
        """Test handling events."""
        handler = ConcreteEventHandler("test.handler")
        event = ConcreteEvent("test", "test.source")
        
        await handler.handle(event)
        
        assert len(handler.handled_events) == 1
        assert handler.handled_events[0] == event
    
    def test_handler_string_representation(self):
        """Test string representation of handler."""
        handler = ConcreteEventHandler("test.handler")
        
        str_repr = str(handler)
        assert "ConcreteEventHandler" in str_repr
        assert "test.handler" in str_repr
        assert "enabled" in str_repr
        
        handler.disable()
        str_repr = str(handler)
        assert "disabled" in str_repr
