"""
Field descriptor system for the Joyride DNS Service event types.

This module provides declarative field descriptors to replace repetitive
@property methods with reusable, composable field definitions.
"""

from typing import Any, Callable, Optional, Type, Union


class EventField:
    """
    Descriptor for declarative event field access with validation and defaults.

    Eliminates repetitive @property methods by providing a reusable descriptor
    that handles data access, type validation, and default values.
    """

    def __init__(
        self,
        data_key: str,
        field_type: Type = str,
        default: Any = None,
        required: bool = True,
        validator: Optional[Callable[[Any], bool]] = None,
        doc: Optional[str] = None,
    ):
        """
        Initialize an event field descriptor.

        Args:
            data_key: Key in the event's data dictionary
            field_type: Expected type of the field value
            default: Default value if field is missing (implies not required)
            required: Whether the field is required (ignored if default provided)
            validator: Optional custom validation function
            doc: Documentation string for the field
        """
        self.data_key = data_key
        self.field_type = field_type
        self.default = default
        self.required = required if default is None else False
        self.validator = validator
        self.doc = doc or f"Get {data_key}."

        # Store the attribute name (set by __set_name__)
        self.name = None

    def __set_name__(self, owner: Type, name: str) -> None:
        """Called when the descriptor is assigned to a class attribute."""
        self.name = name

    def __get__(self, obj: Any, objtype: Optional[Type] = None) -> Any:
        """Get the field value from the event's data dictionary."""
        if obj is None:
            return self

        # Get value from event data
        value = obj.data.get(self.data_key, self.default)

        # Handle required fields
        if value is None and self.required:
            raise ValueError(f"Required field '{self.data_key}' is missing")

        # Return default if no value and not required
        if value is None:
            return self.default

        # Type validation
        if value is not None and not isinstance(value, self.field_type):
            # Try to convert if possible
            try:
                value = self.field_type(value)
            except (ValueError, TypeError) as e:
                raise TypeError(
                    f"Field '{self.data_key}' expected {self.field_type.__name__}, "
                    f"got {type(value).__name__}: {e}"
                )

        # Custom validation
        if self.validator and value is not None:
            if not self.validator(value):
                raise ValueError(
                    f"Field '{self.data_key}' validation failed for value: {value}"
                )

        return value

    def __set__(self, obj: Any, value: Any) -> None:
        """Set the field value in the event's data dictionary."""
        # Type validation
        if value is not None and not isinstance(value, self.field_type):
            try:
                value = self.field_type(value)
            except (ValueError, TypeError) as e:
                raise TypeError(
                    f"Field '{self.data_key}' expected {self.field_type.__name__}, "
                    f"got {type(value).__name__}: {e}"
                )

        # Custom validation
        if self.validator and value is not None:
            if not self.validator(value):
                raise ValueError(
                    f"Field '{self.data_key}' validation failed for value: {value}"
                )

        # Set in data dictionary
        obj.data[self.data_key] = value

    def validate(self, value: Any) -> bool:
        """
        Validate a field value without setting it.

        Args:
            value: Value to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Type validation
            if value is not None and not isinstance(value, self.field_type):
                value = self.field_type(value)

            # Custom validation
            if self.validator and value is not None:
                return self.validator(value)

            return True
        except (ValueError, TypeError):
            return False


class StringField(EventField):
    """String field with optional length validation."""

    def __init__(
        self,
        data_key: str,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize a string field.

        Args:
            data_key: Key in the event's data dictionary
            max_length: Maximum allowed string length
            min_length: Minimum required string length
            **kwargs: Additional EventField arguments
        """

        def length_validator(value: str) -> bool:
            if min_length is not None and len(value) < min_length:
                return False
            if max_length is not None and len(value) > max_length:
                return False
            return True

        # Combine custom validator with length validator
        original_validator = kwargs.get("validator")
        if original_validator:

            def combined_validator(value: str) -> bool:
                return length_validator(value) and original_validator(value)

            kwargs["validator"] = combined_validator
        else:
            kwargs["validator"] = length_validator

        super().__init__(data_key, field_type=str, **kwargs)


class IntField(EventField):
    """Integer field with optional range validation."""

    def __init__(
        self,
        data_key: str,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize an integer field.

        Args:
            data_key: Key in the event's data dictionary
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            **kwargs: Additional EventField arguments
        """

        def range_validator(value: int) -> bool:
            if min_value is not None and value < min_value:
                return False
            if max_value is not None and value > max_value:
                return False
            return True

        # Combine custom validator with range validator
        original_validator = kwargs.get("validator")
        if original_validator:

            def combined_validator(value: int) -> bool:
                return range_validator(value) and original_validator(value)

            kwargs["validator"] = combined_validator
        else:
            kwargs["validator"] = range_validator

        super().__init__(data_key, field_type=int, **kwargs)


class ChoiceField(EventField):
    """Field that validates against a set of allowed choices."""

    def __init__(self, data_key: str, choices: Union[list, set, tuple], **kwargs):
        """
        Initialize a choice field.

        Args:
            data_key: Key in the event's data dictionary
            choices: Allowed values for the field
            **kwargs: Additional EventField arguments
        """
        choices_set = set(choices)

        def choice_validator(value: Any) -> bool:
            return value in choices_set

        # Combine custom validator with choice validator
        original_validator = kwargs.get("validator")
        if original_validator:

            def combined_validator(value: Any) -> bool:
                return choice_validator(value) and original_validator(value)

            kwargs["validator"] = combined_validator
        else:
            kwargs["validator"] = choice_validator

        super().__init__(data_key, **kwargs)


class DictField(EventField):
    """Dictionary field with optional key validation."""

    def __init__(self, data_key: str, **kwargs):
        """
        Initialize a dictionary field.

        Args:
            data_key: Key in the event's data dictionary
            **kwargs: Additional EventField arguments
        """
        kwargs.setdefault("default", {})
        super().__init__(data_key, field_type=dict, **kwargs)


class OptionalField(EventField):
    """Optional field that can be None."""

    def __init__(self, data_key: str, field_type: Type = str, **kwargs):
        """
        Initialize an optional field.

        Args:
            data_key: Key in the event's data dictionary
            field_type: Expected type when not None
            **kwargs: Additional EventField arguments
        """
        kwargs.setdefault("default", None)
        kwargs.setdefault("required", False)
        super().__init__(data_key, field_type=field_type, **kwargs)
