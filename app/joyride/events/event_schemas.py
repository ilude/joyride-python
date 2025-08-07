"""
Event schema composition system for declarative event definitions.

This module provides the EventSchema class and related utilities for defining
event structures in a declarative manner using field descriptors and validation mixins.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union

from .fields import EventField
from .validation_mixins import ValidationMixin


@dataclass
class SchemaField:
    """Represents a field definition within an event schema."""

    name: str
    field_descriptor: EventField
    required: bool = True
    default: Any = None
    validators: List[ValidationMixin] = field(default_factory=list)

    def validate(self, value: Any) -> Any:
        """Validate a value using all configured validators."""
        for validator in self.validators:
            value = validator.validate(value)
        return value


class EventSchemaMeta(type):
    """Metaclass for EventSchema that processes field descriptors."""

    def __new__(cls, name: str, bases: tuple, namespace: dict):
        # Collect field descriptors from class definition
        schema_fields = {}

        # Process fields from base classes first
        for base in bases:
            if hasattr(base, "_schema_fields"):
                schema_fields.update(base._schema_fields)

        # Process fields from current class
        for attr_name, attr_value in list(namespace.items()):
            if isinstance(attr_value, EventField):
                # Convert EventField to SchemaField
                # Use the field's own required property (which accounts for defaults)
                schema_field = SchemaField(
                    name=attr_name,
                    field_descriptor=attr_value,
                    required=attr_value.required,
                    default=attr_value.default,
                    validators=getattr(attr_value, "validators", []),
                )
                schema_fields[attr_name] = schema_field

                # Remove the descriptor from the namespace to avoid conflicts
                del namespace[attr_name]

        # Store schema fields in the class
        namespace["_schema_fields"] = schema_fields

        return super().__new__(cls, name, bases, namespace)


class EventSchema(metaclass=EventSchemaMeta):
    """
    Base class for declarative event schema definitions.

    This class uses field descriptors and validation mixins to provide
    a declarative way to define event structures with automatic validation
    and data handling.

    Example:
        class ContainerEventSchema(EventSchema):
            container_id = StringField(validators=[RequiredValidator()])
            container_name = StringField(max_length=255)
            port = NumericField(min_value=1, max_value=65535)
            status = ChoiceField(choices=['started', 'stopped'])
    """

    _schema_fields: Dict[str, SchemaField] = {}

    def __init__(self, **kwargs):
        """Initialize the event schema with provided data."""
        self._data = {}
        self._errors = {}

        # Process all schema fields
        for field_name, schema_field in self._schema_fields.items():
            if field_name in kwargs:
                # Validate and set provided value
                try:
                    validated_value = schema_field.validate(kwargs[field_name])
                    self._data[field_name] = validated_value
                except Exception as e:
                    self._errors[field_name] = str(e)
                    if schema_field.required and schema_field.default is None:
                        raise ValueError(
                            f"Invalid value for required field '{field_name}': {e}"
                        )
            elif schema_field.required and schema_field.default is None:
                self._errors[field_name] = "Required field missing"
                raise ValueError(f"Required field '{field_name}' is missing")
            elif schema_field.default is not None:
                # Set default value
                self._data[field_name] = schema_field.default

        # Store any extra fields that aren't in the schema
        for key, value in kwargs.items():
            if key not in self._schema_fields:
                self._data[key] = value

    def __getattr__(self, name: str) -> Any:
        """Provide attribute access to schema data."""
        if name.startswith("_"):
            return super().__getattribute__(name)

        if name in self._data:
            return self._data[name]

        if name in self._schema_fields:
            schema_field = self._schema_fields[name]
            if schema_field.default is not None:
                return schema_field.default

        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Provide attribute setting with validation."""
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        if name in self._schema_fields:
            schema_field = self._schema_fields[name]
            try:
                validated_value = schema_field.validate(value)
                self._data[name] = validated_value
                # Clear any previous errors for this field
                if name in self._errors:
                    del self._errors[name]
            except Exception as e:
                self._errors[name] = str(e)
                raise ValueError(f"Invalid value for field '{name}': {e}")
        else:
            # Allow setting of non-schema fields
            if not hasattr(self, "_data"):
                super().__setattr__(name, value)
            else:
                self._data[name] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema instance to a dictionary."""
        return self._data.copy()

    def validate(self) -> bool:
        """Validate all fields and return True if valid."""
        self._errors.clear()

        for field_name, schema_field in self._schema_fields.items():
            if field_name in self._data:
                try:
                    validated_value = schema_field.validate(self._data[field_name])
                    self._data[field_name] = validated_value
                except Exception as e:
                    self._errors[field_name] = str(e)
            elif schema_field.required and schema_field.default is None:
                self._errors[field_name] = "Required field missing"

        return len(self._errors) == 0

    @property
    def errors(self) -> Dict[str, str]:
        """Get validation errors."""
        return self._errors.copy()

    @property
    def is_valid(self) -> bool:
        """Check if the schema instance is valid."""
        return len(self._errors) == 0

    @classmethod
    def get_field_names(cls) -> List[str]:
        """Get a list of all field names in the schema."""
        return list(cls._schema_fields.keys())

    @classmethod
    def get_required_fields(cls) -> List[str]:
        """Get a list of required field names."""
        return [name for name, field in cls._schema_fields.items() if field.required]

    @classmethod
    def get_field_info(cls, field_name: str) -> Optional[SchemaField]:
        """Get information about a specific field."""
        return cls._schema_fields.get(field_name)


# Schema factory for creating schemas at runtime
class SchemaFactory:
    """Factory for creating event schemas dynamically."""

    @staticmethod
    def create_schema(
        name: str,
        fields: Dict[str, Union[EventField, tuple]],
        base_classes: Optional[tuple] = None,
    ) -> Type[EventSchema]:
        """
        Create an event schema class dynamically.

        Args:
            name: Name of the schema class
            fields: Dictionary of field definitions
            base_classes: Optional base classes to inherit from

        Returns:
            A new EventSchema class
        """
        if base_classes is None:
            base_classes = (EventSchema,)

        # Process fields into EventField instances
        processed_fields = {}
        for field_name, field_def in fields.items():
            if isinstance(field_def, EventField):
                processed_fields[field_name] = field_def
            elif isinstance(field_def, tuple):
                # Handle tuple definitions like (field_type, validators, default)
                field_type, *args = field_def
                if issubclass(field_type, EventField):
                    processed_fields[field_name] = field_type(*args)
                else:
                    raise ValueError(
                        f"Invalid field type for '{field_name}': {field_type}"
                    )
            else:
                raise ValueError(
                    f"Invalid field definition for '{field_name}': {field_def}"
                )

        # Create the class
        return type(name, base_classes, processed_fields)


# Schema validation utilities
class SchemaValidator:
    """Utilities for schema validation and error handling."""

    @staticmethod
    def validate_data(schema_class: Type[EventSchema], data: Dict[str, Any]) -> tuple:
        """
        Validate data against a schema without creating an instance.

        Returns:
            Tuple of (is_valid, validated_data, errors)
        """
        try:
            schema_instance = schema_class(**data)
            return True, schema_instance.to_dict(), {}
        except ValueError as e:
            return False, {}, {"validation_error": str(e)}

    @staticmethod
    def merge_schemas(
        schema1: Type[EventSchema], schema2: Type[EventSchema], name: str
    ) -> Type[EventSchema]:
        """
        Merge two schemas into a new schema class.

        Args:
            schema1: First schema to merge
            schema2: Second schema to merge (takes precedence)
            name: Name for the merged schema

        Returns:
            A new merged schema class
        """
        merged_fields = {}

        # Add fields from schema1
        if hasattr(schema1, "_schema_fields"):
            for field_name, schema_field in schema1._schema_fields.items():
                merged_fields[field_name] = schema_field.field_descriptor

        # Add fields from schema2 (overwrites schema1 if conflicts)
        if hasattr(schema2, "_schema_fields"):
            for field_name, schema_field in schema2._schema_fields.items():
                merged_fields[field_name] = schema_field.field_descriptor

        return SchemaFactory.create_schema(name, merged_fields, (schema1, schema2))
