"""
Tests for the event field descriptor system.

Tests EventField descriptors for property access, type validation, and default values.
"""

import pytest

from app.joyride.events.fields import (
    ChoiceField,
    DictField,
    EventField,
    IntField,
    OptionalField,
    StringField,
)


class MockEvent:
    """Mock event class for testing field descriptors."""

    def __init__(self, data=None):
        """Initialize mock event with data dictionary."""
        self.data = data or {}


class TestEventField:
    """Test basic EventField functionality."""

    def test_field_creation(self):
        """Test creating an EventField descriptor."""
        field = EventField("test_key", field_type=str, doc="Test field")

        assert field.data_key == "test_key"
        assert field.field_type == str
        assert field.doc == "Test field"
        assert field.required is True
        assert field.default is None

    def test_field_with_default(self):
        """Test creating field with default value."""
        field = EventField("test_key", default="default_value")

        assert field.required is False  # Default implies not required
        assert field.default == "default_value"

    def test_basic_field_access(self):
        """Test basic field get/set operations."""

        class TestEvent:
            test_field = EventField("test_key", field_type=str)

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Set value
        event.test_field = "test_value"
        assert event.data["test_key"] == "test_value"

        # Get value
        assert event.test_field == "test_value"

    def test_required_field_validation(self):
        """Test required field validation."""

        class TestEvent:
            required_field = EventField("required_key", required=True)

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Should raise error for missing required field
        with pytest.raises(
            ValueError, match="Required field 'required_key' is missing"
        ):
            _ = event.required_field

    def test_default_value_handling(self):
        """Test default value handling."""

        class TestEvent:
            optional_field = EventField("optional_key", default="default_val")

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Should return default when not set
        assert event.optional_field == "default_val"

    def test_type_validation(self):
        """Test type validation and conversion."""

        class TestEvent:
            int_field = EventField("int_key", field_type=int)

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Valid integer
        event.int_field = 42
        assert event.int_field == 42

        # String that can be converted to int
        event.int_field = "123"
        assert event.int_field == 123
        assert isinstance(event.int_field, int)

        # Invalid conversion should raise TypeError
        with pytest.raises(TypeError, match="expected int"):
            event.int_field = "not_a_number"

    def test_custom_validator(self):
        """Test custom validation functions."""

        def positive_validator(value):
            return value > 0

        class TestEvent:
            positive_field = EventField(
                "pos_key", field_type=int, validator=positive_validator
            )

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Valid positive value
        event.positive_field = 5
        assert event.positive_field == 5

        # Invalid negative value
        with pytest.raises(ValueError, match="validation failed"):
            event.positive_field = -1

    def test_field_validation_method(self):
        """Test the validate method."""
        field = EventField("test_key", field_type=int)

        # Valid values
        assert field.validate(42) is True
        assert field.validate("123") is True  # Can be converted

        # Invalid values
        assert field.validate("not_a_number") is False

    def test_descriptor_access_on_class(self):
        """Test accessing descriptor from class (not instance)."""

        class TestEvent:
            test_field = EventField("test_key")

        # Should return the descriptor itself when accessed from class
        assert isinstance(TestEvent.test_field, EventField)


class TestStringField:
    """Test StringField functionality."""

    def test_string_field_creation(self):
        """Test creating a StringField."""
        field = StringField("name", max_length=50, min_length=1)

        assert field.field_type == str
        assert field.data_key == "name"

    def test_length_validation(self):
        """Test string length validation."""

        class TestEvent:
            name_field = StringField("name", max_length=10, min_length=2)

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Valid length
        event.name_field = "valid"
        assert event.name_field == "valid"

        # Too short
        with pytest.raises(ValueError, match="validation failed"):
            event.name_field = "x"

        # Too long
        with pytest.raises(ValueError, match="validation failed"):
            event.name_field = "this_is_too_long"

    def test_string_field_with_custom_validator(self):
        """Test StringField with additional custom validator."""

        def email_validator(value):
            return "@" in value and "." in value

        class TestEvent:
            email_field = StringField("email", validator=email_validator)

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Valid email-like string
        event.email_field = "test@example.com"
        assert event.email_field == "test@example.com"

        # Invalid email
        with pytest.raises(ValueError, match="validation failed"):
            event.email_field = "not_an_email"


class TestIntField:
    """Test IntField functionality."""

    def test_int_field_creation(self):
        """Test creating an IntField."""
        field = IntField("port", min_value=1, max_value=65535)

        assert field.field_type == int
        assert field.data_key == "port"

    def test_range_validation(self):
        """Test integer range validation."""

        class TestEvent:
            port_field = IntField("port", min_value=1, max_value=65535)

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Valid port
        event.port_field = 8080
        assert event.port_field == 8080

        # Below minimum
        with pytest.raises(ValueError, match="validation failed"):
            event.port_field = 0

        # Above maximum
        with pytest.raises(ValueError, match="validation failed"):
            event.port_field = 70000

    def test_int_field_with_custom_validator(self):
        """Test IntField with additional custom validator."""

        def even_validator(value):
            return value % 2 == 0

        class TestEvent:
            even_field = IntField("even_num", validator=even_validator)

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Valid even number
        event.even_field = 42
        assert event.even_field == 42

        # Invalid odd number
        with pytest.raises(ValueError, match="validation failed"):
            event.even_field = 43


class TestChoiceField:
    """Test ChoiceField functionality."""

    def test_choice_field_creation(self):
        """Test creating a ChoiceField."""
        choices = ["A", "AAAA", "CNAME", "MX"]
        field = ChoiceField("record_type", choices=choices)

        assert field.data_key == "record_type"

    def test_choice_validation(self):
        """Test choice validation."""

        class TestEvent:
            record_type = ChoiceField("record_type", choices=["A", "AAAA", "CNAME"])

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Valid choice
        event.record_type = "A"
        assert event.record_type == "A"

        # Invalid choice
        with pytest.raises(ValueError, match="validation failed"):
            event.record_type = "INVALID"

    def test_choice_field_with_custom_validator(self):
        """Test ChoiceField with additional custom validator."""

        def uppercase_validator(value):
            return value.isupper()

        class TestEvent:
            status_field = ChoiceField(
                "status", choices=["OK", "ERROR", "WARN"], validator=uppercase_validator
            )

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Valid uppercase choice
        event.status_field = "OK"
        assert event.status_field == "OK"

        # Valid choice but not uppercase (should fail custom validator)
        # Note: This would fail the choices first, so let's test with lowercase choices
        class TestEvent2:
            status_field = ChoiceField(
                "status", choices=["ok", "error"], validator=uppercase_validator
            )

            def __init__(self):
                self.data = {}

        event2 = TestEvent2()

        with pytest.raises(ValueError, match="validation failed"):
            event2.status_field = "ok"  # Valid choice but fails uppercase validator


class TestDictField:
    """Test DictField functionality."""

    def test_dict_field_creation(self):
        """Test creating a DictField."""
        field = DictField("metadata")

        assert field.field_type == dict
        assert field.default == {}

    def test_dict_field_default(self):
        """Test DictField default behavior."""

        class TestEvent:
            metadata_field = DictField("metadata")

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Should return empty dict by default
        assert event.metadata_field == {}

        # Should be able to set dict
        test_dict = {"key": "value"}
        event.metadata_field = test_dict
        assert event.metadata_field == test_dict


class TestOptionalField:
    """Test OptionalField functionality."""

    def test_optional_field_creation(self):
        """Test creating an OptionalField."""
        field = OptionalField("optional_value", field_type=int)

        assert field.field_type == int
        assert field.default is None
        assert field.required is False

    def test_optional_field_behavior(self):
        """Test OptionalField None handling."""

        class TestEvent:
            optional_field = OptionalField("optional_val", field_type=str)

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Should return None by default
        assert event.optional_field is None

        # Should be able to set value
        event.optional_field = "test_value"
        assert event.optional_field == "test_value"

        # Should be able to set back to None
        event.optional_field = None
        assert event.optional_field is None


class TestFieldIntegration:
    """Test field descriptors in realistic event scenarios."""

    def test_multiple_fields_in_event(self):
        """Test multiple different field types in one event class."""

        class TestEvent:
            container_id = StringField("container_id", min_length=1)
            port = IntField("port", min_value=1, max_value=65535)
            status = ChoiceField("status", choices=["running", "stopped", "paused"])
            metadata = DictField("metadata")
            description = OptionalField("description", field_type=str)

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Set all fields
        event.container_id = "container_123"
        event.port = 8080
        event.status = "running"
        event.metadata = {"env": "prod"}
        event.description = "Test container"

        # Verify all fields
        assert event.container_id == "container_123"
        assert event.port == 8080
        assert event.status == "running"
        assert event.metadata == {"env": "prod"}
        assert event.description == "Test container"

    def test_field_validation_integration(self):
        """Test field validation works together."""

        class TestEvent:
            name = StringField("name", min_length=2, max_length=10)
            priority = IntField("priority", min_value=1, max_value=10)

            def __init__(self):
                self.data = {}

        event = TestEvent()

        # Valid values
        event.name = "test"
        event.priority = 5

        # Invalid name (too short)
        with pytest.raises(ValueError):
            event.name = "x"

        # Invalid priority (too high)
        with pytest.raises(ValueError):
            event.priority = 15


if __name__ == "__main__":
    pytest.main([__file__])
