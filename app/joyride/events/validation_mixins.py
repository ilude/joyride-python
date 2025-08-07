"""
Validation mixins for the Joyride DNS Service event system.

This module provides reusable validation components to replace repetitive
validation code with composable mixin classes.
"""

import re
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Pattern, Set, Union


class ValidationMixin(ABC):
    """
    Base class for validation mixins.

    Provides a common interface for all validation mixins used in the
    event system.
    """

    @abstractmethod
    def validate(self, value: Any, field_name: str) -> None:
        """
        Validate a field value.

        Args:
            value: The value to validate
            field_name: Name of the field being validated (for error messages)

        Raises:
            ValueError: If validation fails
        """
        pass


class StringValidator(ValidationMixin):
    """
    Mixin for string validation with configurable constraints.

    Provides validation for:
    - Empty string checks
    - Minimum and maximum length validation
    - Pattern matching with regex
    - Whitespace trimming options
    """

    def __init__(
        self,
        allow_empty: bool = False,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[Union[str, Pattern[str]]] = None,
        strip_whitespace: bool = True,
    ):
        """
        Initialize string validator.

        Args:
            allow_empty: Whether to allow empty strings
            min_length: Minimum required length
            max_length: Maximum allowed length
            pattern: Regex pattern the string must match
            strip_whitespace: Whether to strip whitespace before validation
        """
        self.allow_empty = allow_empty
        self.min_length = min_length
        self.max_length = max_length
        self.strip_whitespace = strip_whitespace

        # Compile pattern if it's a string
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern)
        else:
            self.pattern = pattern

    def validate(self, value: Any, field_name: str) -> None:
        """Validate string field."""
        if value is None:
            if not self.allow_empty:
                raise ValueError(f"{field_name} cannot be None")
            return

        if not isinstance(value, str):
            raise ValueError(
                f"{field_name} must be a string, got {type(value).__name__}"
            )

        # Strip whitespace if configured
        original_value = value
        if self.strip_whitespace:
            value = value.strip()

        # Check empty string
        if not value and not self.allow_empty:
            raise ValueError(f"{field_name} cannot be empty")

        # Use original value for length checks if not stripping
        check_value = value if self.strip_whitespace else original_value

        # Check minimum length
        if self.min_length is not None and len(check_value) < self.min_length:
            raise ValueError(
                f"{field_name} must be at least {self.min_length} characters long"
            )

        # Check maximum length
        if self.max_length is not None and len(check_value) > self.max_length:
            raise ValueError(
                f"{field_name} must be at most {self.max_length} characters long"
            )

        # Check pattern match - use processed value for pattern matching
        if self.pattern and not self.pattern.match(value):
            raise ValueError(f"{field_name} does not match required pattern")


class NumericValidator(ValidationMixin):
    """
    Mixin for numeric validation with configurable constraints.

    Provides validation for:
    - Type checking (int, float, or both)
    - Minimum and maximum value validation
    - Positive/negative constraints
    - Zero inclusion/exclusion
    """

    def __init__(
        self,
        numeric_type: Union[type, tuple] = (int, float),
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        allow_zero: bool = True,
        positive_only: bool = False,
        negative_only: bool = False,
    ):
        """
        Initialize numeric validator.

        Args:
            numeric_type: Allowed numeric types (int, float, or tuple of both)
            min_value: Minimum allowed value (inclusive)
            max_value: Maximum allowed value (inclusive)
            allow_zero: Whether zero is allowed
            positive_only: Whether only positive values are allowed
            negative_only: Whether only negative values are allowed
        """
        self.numeric_type = numeric_type
        self.min_value = min_value
        self.max_value = max_value
        self.allow_zero = allow_zero
        self.positive_only = positive_only
        self.negative_only = negative_only

        # Validate conflicting options
        if positive_only and negative_only:
            raise ValueError("Cannot specify both positive_only and negative_only")

    def validate(self, value: Any, field_name: str) -> None:
        """Validate numeric field."""
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        # Type validation
        if not isinstance(value, self.numeric_type):
            expected_types = (
                self.numeric_type.__name__
                if isinstance(self.numeric_type, type)
                else " or ".join(t.__name__ for t in self.numeric_type)
            )
            raise ValueError(
                f"{field_name} must be {expected_types}, got {type(value).__name__}"
            )

        # Zero validation
        if value == 0 and not self.allow_zero:
            raise ValueError(f"{field_name} cannot be zero")

        # Positive/negative validation
        if self.positive_only and value <= 0:
            raise ValueError(f"{field_name} must be positive")

        if self.negative_only and value >= 0:
            raise ValueError(f"{field_name} must be negative")

        # Range validation
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"{field_name} must be at least {self.min_value}")

        if self.max_value is not None and value > self.max_value:
            raise ValueError(f"{field_name} must be at most {self.max_value}")


class ChoiceValidator(ValidationMixin):
    """
    Mixin for choice validation against a set of allowed values.

    Provides validation for:
    - Membership in allowed choices
    - Case-sensitive/insensitive matching
    - Type conversion before validation
    """

    def __init__(
        self,
        choices: Union[List, Set, tuple],
        case_sensitive: bool = True,
        allow_none: bool = False,
    ):
        """
        Initialize choice validator.

        Args:
            choices: Collection of allowed values
            case_sensitive: Whether string matching is case-sensitive
            allow_none: Whether None is considered a valid choice
        """
        self.case_sensitive = case_sensitive
        self.allow_none = allow_none

        # Convert choices to set for efficient lookup
        if case_sensitive or not all(isinstance(c, str) for c in choices):
            self.choices = set(choices)
        else:
            # Case-insensitive: store lowercase versions
            self.choices = {c.lower() if isinstance(c, str) else c for c in choices}
            self.original_choices = set(choices)  # Keep originals for error messages

    def validate(self, value: Any, field_name: str) -> None:
        """Validate choice field."""
        if value is None:
            if self.allow_none:
                return
            raise ValueError(f"{field_name} cannot be None")

        # Handle case-insensitive string comparison
        if not self.case_sensitive and isinstance(value, str):
            check_value = value.lower()
            choices_for_check = self.choices
            choices_for_error = getattr(self, "original_choices", self.choices)
        else:
            check_value = value
            choices_for_check = self.choices
            choices_for_error = self.choices

        if check_value not in choices_for_check:
            # Handle mixed type sorting by converting to strings
            try:
                choices_str = ", ".join(str(c) for c in sorted(choices_for_error))
            except TypeError:
                # If sorting fails due to mixed types, don't sort
                choices_str = ", ".join(str(c) for c in choices_for_error)
            raise ValueError(f"{field_name} must be one of: {choices_str}")


class IPAddressValidator(ValidationMixin):
    """
    Mixin for IP address validation.

    Provides validation for:
    - IPv4 address format
    - IPv6 address format
    - CIDR notation support
    """

    def __init__(
        self,
        allow_ipv4: bool = True,
        allow_ipv6: bool = True,
        allow_cidr: bool = False,
    ):
        """
        Initialize IP address validator.

        Args:
            allow_ipv4: Whether IPv4 addresses are allowed
            allow_ipv6: Whether IPv6 addresses are allowed
            allow_cidr: Whether CIDR notation is allowed
        """
        self.allow_ipv4 = allow_ipv4
        self.allow_ipv6 = allow_ipv6
        self.allow_cidr = allow_cidr

        if not (allow_ipv4 or allow_ipv6):
            raise ValueError("Must allow at least one IP version")

        # IPv4 pattern (basic validation)
        self.ipv4_pattern = re.compile(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        )

        # IPv6 pattern (covers common IPv6 formats)
        self.ipv6_pattern = re.compile(
            r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$|"  # Standard and compressed
            r"^::1$|^::$|"  # Loopback and any
            r"^[0-9a-fA-F]{1,4}::([0-9a-fA-F]{1,4}:)*[0-9a-fA-F]{0,4}$"  # Leading compression
        )

        # CIDR pattern
        self.cidr_pattern = re.compile(r"^(.+)/(\d+)$")

    def validate(self, value: Any, field_name: str) -> None:
        """Validate IP address field."""
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")

        value = value.strip()
        if not value:
            raise ValueError(f"{field_name} cannot be empty")

        # Handle CIDR notation
        if self.allow_cidr and "/" in value:
            match = self.cidr_pattern.match(value)
            if not match:
                raise ValueError(f"{field_name} has invalid CIDR format")

            ip_part, prefix_part = match.groups()

            # Validate prefix length
            try:
                prefix_len = int(prefix_part)
            except ValueError:
                raise ValueError(f"{field_name} has invalid CIDR prefix")

            # Check prefix length based on IP version
            if self._is_ipv4(ip_part):
                if not (0 <= prefix_len <= 32):
                    raise ValueError(f"{field_name} IPv4 CIDR prefix must be 0-32")
            elif self._is_ipv6(ip_part):
                if not (0 <= prefix_len <= 128):
                    raise ValueError(f"{field_name} IPv6 CIDR prefix must be 0-128")

            # Validate the IP part
            value = ip_part

        # Validate IP address
        is_ipv4 = self._is_ipv4(value)
        is_ipv6 = self._is_ipv6(value)

        if is_ipv4 and self.allow_ipv4:
            return
        elif is_ipv6 and self.allow_ipv6:
            return
        elif is_ipv4 and not self.allow_ipv4:
            raise ValueError(f"{field_name} IPv4 addresses are not allowed")
        elif is_ipv6 and not self.allow_ipv6:
            raise ValueError(f"{field_name} IPv6 addresses are not allowed")
        else:
            allowed_versions = []
            if self.allow_ipv4:
                allowed_versions.append("IPv4")
            if self.allow_ipv6:
                allowed_versions.append("IPv6")
            versions_str = " or ".join(allowed_versions)
            raise ValueError(f"{field_name} must be a valid {versions_str} address")

    def _is_ipv4(self, value: str) -> bool:
        """Check if value is a valid IPv4 address."""
        return bool(self.ipv4_pattern.match(value))

    def _is_ipv6(self, value: str) -> bool:
        """Check if value is a valid IPv6 address."""
        return bool(self.ipv6_pattern.match(value))


class CompositeValidator(ValidationMixin):
    """
    Mixin that combines multiple validators.

    Allows applying multiple validation rules to a single field.
    Validators are applied in the order they were added.
    """

    def __init__(self, validators: List[ValidationMixin]):
        """
        Initialize composite validator.

        Args:
            validators: List of validators to apply in sequence
        """
        self.validators = validators

    def validate(self, value: Any, field_name: str) -> None:
        """Apply all validators in sequence."""
        for validator in self.validators:
            validator.validate(value, field_name)


# Predefined common validators for convenience
DNS_RECORD_TYPE_VALIDATOR = ChoiceValidator(
    choices=["A", "AAAA", "CNAME", "MX", "NS", "PTR", "SOA", "SRV", "TXT"],
    case_sensitive=False,
)

HEALTH_STATUS_VALIDATOR = ChoiceValidator(
    choices=["healthy", "degraded", "unhealthy"], case_sensitive=False
)

ERROR_SEVERITY_VALIDATOR = ChoiceValidator(
    choices=["debug", "info", "warning", "error", "critical"], case_sensitive=False
)

POSITIVE_INTEGER_VALIDATOR = NumericValidator(numeric_type=int, positive_only=True)

NON_NEGATIVE_INTEGER_VALIDATOR = NumericValidator(numeric_type=int, min_value=0)

NON_EMPTY_STRING_VALIDATOR = StringValidator(allow_empty=False)

HOSTNAME_VALIDATOR = StringValidator(
    allow_empty=False,
    max_length=253,
    pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$",
)

IPV4_VALIDATOR = IPAddressValidator(allow_ipv4=True, allow_ipv6=False)
