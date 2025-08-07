"""
Tests for validation mixins in the Joyride DNS Service event system.

This module tests the validation mixin classes that provide reusable
validation components for event fields.
"""

import re

import pytest

from app.joyride.events.validation_mixins import (
    DNS_RECORD_TYPE_VALIDATOR,
    ERROR_SEVERITY_VALIDATOR,
    HEALTH_STATUS_VALIDATOR,
    HOSTNAME_VALIDATOR,
    IPV4_VALIDATOR,
    NON_EMPTY_STRING_VALIDATOR,
    NON_NEGATIVE_INTEGER_VALIDATOR,
    POSITIVE_INTEGER_VALIDATOR,
    ChoiceValidator,
    CompositeValidator,
    IPAddressValidator,
    NumericValidator,
    StringValidator,
    ValidationMixin,
)


class TestStringValidator:
    """Test StringValidator mixin."""

    def test_basic_string_validation(self):
        """Test basic string validation."""
        validator = StringValidator()

        # Valid strings
        validator.validate("test", "field")
        validator.validate("hello world", "field")

        # Invalid types
        with pytest.raises(ValueError, match="field must be a string"):
            validator.validate(123, "field")

        with pytest.raises(ValueError, match="field must be a string"):
            validator.validate([], "field")

    def test_empty_string_validation(self):
        """Test empty string validation."""
        # Default: empty not allowed
        validator = StringValidator()
        with pytest.raises(ValueError, match="field cannot be empty"):
            validator.validate("", "field")
        with pytest.raises(ValueError, match="field cannot be empty"):
            validator.validate("   ", "field")  # Whitespace stripped

        # Allow empty
        validator = StringValidator(allow_empty=True)
        validator.validate("", "field")
        validator.validate("   ", "field")

    def test_none_validation(self):
        """Test None value validation."""
        # Default: None not allowed
        validator = StringValidator()
        with pytest.raises(ValueError, match="field cannot be None"):
            validator.validate(None, "field")

        # Allow empty (includes None)
        validator = StringValidator(allow_empty=True)
        validator.validate(None, "field")

    def test_length_validation(self):
        """Test string length validation."""
        validator = StringValidator(min_length=3, max_length=10)

        # Valid lengths
        validator.validate("abc", "field")
        validator.validate("hello", "field")
        validator.validate("1234567890", "field")

        # Too short
        with pytest.raises(ValueError, match="field must be at least 3 characters"):
            validator.validate("ab", "field")

        # Too long
        with pytest.raises(ValueError, match="field must be at most 10 characters"):
            validator.validate("12345678901", "field")

    def test_pattern_validation(self):
        """Test regex pattern validation."""
        # Email-like pattern
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        validator = StringValidator(pattern=email_pattern)

        # Valid emails
        validator.validate("test@example.com", "email")
        validator.validate("user.name+tag@example.org", "email")

        # Invalid emails
        with pytest.raises(ValueError, match="email does not match required pattern"):
            validator.validate("invalid-email", "email")
        with pytest.raises(ValueError, match="email does not match required pattern"):
            validator.validate("@example.com", "email")

    def test_pattern_as_compiled_regex(self):
        """Test using pre-compiled regex pattern."""
        pattern = re.compile(r"^[0-9]+$")
        validator = StringValidator(pattern=pattern)

        validator.validate("12345", "field")
        with pytest.raises(ValueError, match="field does not match required pattern"):
            validator.validate("abc123", "field")

    def test_whitespace_stripping(self):
        """Test whitespace stripping behavior."""
        # With stripping (default)
        validator = StringValidator(min_length=5)
        validator.validate("  hello  ", "field")  # Becomes "hello" (5 chars)

        # Without stripping
        validator = StringValidator(min_length=5, strip_whitespace=False)
        validator.validate("  hello  ", "field")  # Stays "  hello  " (9 chars)

        with pytest.raises(ValueError, match="field must be at least 5 characters"):
            validator.validate(" hi ", "field")  # Stays " hi " (4 chars, less than 5)


class TestNumericValidator:
    """Test NumericValidator mixin."""

    def test_basic_numeric_validation(self):
        """Test basic numeric validation."""
        validator = NumericValidator()

        # Valid numbers
        validator.validate(42, "field")
        validator.validate(3.14, "field")
        validator.validate(-5, "field")
        validator.validate(0, "field")

        # Invalid types
        with pytest.raises(ValueError, match="field must be int or float"):
            validator.validate("123", "field")
        with pytest.raises(ValueError, match="field must be int or float"):
            validator.validate([], "field")

    def test_none_validation(self):
        """Test None value validation."""
        validator = NumericValidator()
        with pytest.raises(ValueError, match="field cannot be None"):
            validator.validate(None, "field")

    def test_integer_only_validation(self):
        """Test integer-only validation."""
        validator = NumericValidator(numeric_type=int)

        validator.validate(42, "field")
        validator.validate(-5, "field")

        with pytest.raises(ValueError, match="field must be int"):
            validator.validate(3.14, "field")

    def test_float_only_validation(self):
        """Test float-only validation."""
        validator = NumericValidator(numeric_type=float)

        validator.validate(3.14, "field")
        validator.validate(-2.5, "field")

        with pytest.raises(ValueError, match="field must be float"):
            validator.validate(42, "field")

    def test_range_validation(self):
        """Test min/max value validation."""
        validator = NumericValidator(min_value=0, max_value=100)

        # Valid values
        validator.validate(0, "field")
        validator.validate(50, "field")
        validator.validate(100, "field")

        # Out of range
        with pytest.raises(ValueError, match="field must be at least 0"):
            validator.validate(-1, "field")
        with pytest.raises(ValueError, match="field must be at most 100"):
            validator.validate(101, "field")

    def test_zero_validation(self):
        """Test zero value validation."""
        # Allow zero (default)
        validator = NumericValidator()
        validator.validate(0, "field")

        # Disallow zero
        validator = NumericValidator(allow_zero=False)
        with pytest.raises(ValueError, match="field cannot be zero"):
            validator.validate(0, "field")
        with pytest.raises(ValueError, match="field cannot be zero"):
            validator.validate(0.0, "field")

    def test_positive_only_validation(self):
        """Test positive-only validation."""
        validator = NumericValidator(positive_only=True)

        validator.validate(1, "field")
        validator.validate(3.14, "field")

        with pytest.raises(ValueError, match="field must be positive"):
            validator.validate(0, "field")
        with pytest.raises(ValueError, match="field must be positive"):
            validator.validate(-1, "field")

    def test_negative_only_validation(self):
        """Test negative-only validation."""
        validator = NumericValidator(negative_only=True)

        validator.validate(-1, "field")
        validator.validate(-3.14, "field")

        with pytest.raises(ValueError, match="field must be negative"):
            validator.validate(0, "field")
        with pytest.raises(ValueError, match="field must be negative"):
            validator.validate(1, "field")

    def test_conflicting_positive_negative_options(self):
        """Test validation of conflicting options."""
        with pytest.raises(
            ValueError, match="Cannot specify both positive_only and negative_only"
        ):
            NumericValidator(positive_only=True, negative_only=True)


class TestChoiceValidator:
    """Test ChoiceValidator mixin."""

    def test_basic_choice_validation(self):
        """Test basic choice validation."""
        validator = ChoiceValidator(choices=["red", "green", "blue"])

        # Valid choices
        validator.validate("red", "color")
        validator.validate("green", "color")
        validator.validate("blue", "color")

        # Invalid choice
        with pytest.raises(ValueError, match="color must be one of: blue, green, red"):
            validator.validate("yellow", "color")

    def test_none_validation(self):
        """Test None value validation."""
        # Default: None not allowed
        validator = ChoiceValidator(choices=["a", "b"])
        with pytest.raises(ValueError, match="field cannot be None"):
            validator.validate(None, "field")

        # Allow None
        validator = ChoiceValidator(choices=["a", "b"], allow_none=True)
        validator.validate(None, "field")

    def test_case_sensitive_validation(self):
        """Test case-sensitive validation."""
        # Case sensitive (default)
        validator = ChoiceValidator(choices=["Red", "Green", "Blue"])

        validator.validate("Red", "color")

        with pytest.raises(ValueError, match="color must be one of"):
            validator.validate("red", "color")
        with pytest.raises(ValueError, match="color must be one of"):
            validator.validate("RED", "color")

    def test_case_insensitive_validation(self):
        """Test case-insensitive validation."""
        validator = ChoiceValidator(
            choices=["Red", "Green", "Blue"], case_sensitive=False
        )

        # All case variations should work
        validator.validate("Red", "color")
        validator.validate("red", "color")
        validator.validate("RED", "color")
        validator.validate("rEd", "color")

    def test_non_string_choices(self):
        """Test choices with non-string values."""
        validator = ChoiceValidator(choices=[1, 2, 3, "four"])

        validator.validate(1, "field")
        validator.validate(2, "field")
        validator.validate("four", "field")

        with pytest.raises(ValueError, match="field must be one of"):
            validator.validate(5, "field")
        with pytest.raises(ValueError, match="field must be one of"):
            validator.validate("five", "field")

    def test_set_and_tuple_choices(self):
        """Test using set and tuple for choices."""
        # Set
        validator = ChoiceValidator(choices={"a", "b", "c"})
        validator.validate("a", "field")

        # Tuple
        validator = ChoiceValidator(choices=("x", "y", "z"))
        validator.validate("x", "field")


class TestIPAddressValidator:
    """Test IPAddressValidator mixin."""

    def test_ipv4_validation(self):
        """Test IPv4 address validation."""
        validator = IPAddressValidator(allow_ipv4=True, allow_ipv6=False)

        # Valid IPv4
        validator.validate("192.168.1.1", "ip")
        validator.validate("10.0.0.1", "ip")
        validator.validate("255.255.255.255", "ip")
        validator.validate("0.0.0.0", "ip")

        # Invalid IPv4
        with pytest.raises(ValueError, match="ip must be a valid IPv4 address"):
            validator.validate("256.1.1.1", "ip")
        with pytest.raises(ValueError, match="ip must be a valid IPv4 address"):
            validator.validate("192.168.1", "ip")
        with pytest.raises(ValueError, match="ip must be a valid IPv4 address"):
            validator.validate("not-an-ip", "ip")

    def test_ipv6_validation(self):
        """Test IPv6 address validation."""
        validator = IPAddressValidator(allow_ipv4=False, allow_ipv6=True)

        # Valid IPv6
        validator.validate("2001:0db8:85a3:0000:0000:8a2e:0370:7334", "ip")
        validator.validate("::1", "ip")
        validator.validate("::", "ip")
        validator.validate("2001:db8::1", "ip")

        # Invalid IPv6
        with pytest.raises(ValueError, match="ip IPv4 addresses are not allowed"):
            validator.validate("192.168.1.1", "ip")
        with pytest.raises(ValueError, match="ip must be a valid IPv6 address"):
            validator.validate("not-an-ip", "ip")

    def test_dual_stack_validation(self):
        """Test allowing both IPv4 and IPv6."""
        validator = IPAddressValidator(allow_ipv4=True, allow_ipv6=True)

        # Both should work
        validator.validate("192.168.1.1", "ip")
        validator.validate("2001:db8::1", "ip")

    def test_cidr_validation(self):
        """Test CIDR notation validation."""
        validator = IPAddressValidator(allow_cidr=True)

        # Valid CIDR
        validator.validate("192.168.1.0/24", "network")
        validator.validate("10.0.0.0/8", "network")
        validator.validate("2001:db8::/32", "network")

        # Invalid CIDR
        with pytest.raises(ValueError, match="network has invalid CIDR format"):
            validator.validate("192.168.1.1/", "network")
        with pytest.raises(ValueError, match="network has invalid CIDR format"):
            validator.validate("192.168.1.1/abc", "network")
        with pytest.raises(ValueError, match="network IPv4 CIDR prefix must be 0-32"):
            validator.validate("192.168.1.1/33", "network")
        with pytest.raises(ValueError, match="network IPv6 CIDR prefix must be 0-128"):
            validator.validate("2001:db8::/129", "network")

    def test_none_and_empty_validation(self):
        """Test None and empty string validation."""
        validator = IPAddressValidator()

        with pytest.raises(ValueError, match="ip cannot be None"):
            validator.validate(None, "ip")
        with pytest.raises(ValueError, match="ip cannot be empty"):
            validator.validate("", "ip")
        with pytest.raises(ValueError, match="ip cannot be empty"):
            validator.validate("   ", "ip")

    def test_non_string_validation(self):
        """Test non-string value validation."""
        validator = IPAddressValidator()

        with pytest.raises(ValueError, match="ip must be a string"):
            validator.validate(123, "ip")

    def test_invalid_configuration(self):
        """Test invalid validator configuration."""
        with pytest.raises(ValueError, match="Must allow at least one IP version"):
            IPAddressValidator(allow_ipv4=False, allow_ipv6=False)


class TestCompositeValidator:
    """Test CompositeValidator mixin."""

    def test_multiple_validators(self):
        """Test applying multiple validators."""
        string_validator = StringValidator(min_length=3, max_length=10)
        choice_validator = ChoiceValidator(choices=["short", "medium", "long"])

        composite = CompositeValidator([string_validator, choice_validator])

        # Valid value that passes all validators
        composite.validate("short", "field")
        composite.validate("medium", "field")

        # Fails string length validation
        with pytest.raises(ValueError, match="field must be at least 3 characters"):
            composite.validate("hi", "field")

        # Fails choice validation (valid length but invalid choice)
        with pytest.raises(ValueError, match="field must be one of"):
            composite.validate("valid", "field")  # 5 chars, within length limit

    def test_validation_order(self):
        """Test that validators are applied in order."""
        # First validator will catch the error
        validator1 = StringValidator(allow_empty=False)
        validator2 = ChoiceValidator(choices=["test"])

        composite = CompositeValidator([validator1, validator2])

        # Should fail on first validator (empty string)
        with pytest.raises(ValueError, match="field cannot be empty"):
            composite.validate("", "field")

    def test_empty_validator_list(self):
        """Test composite validator with no validators."""
        composite = CompositeValidator([])

        # Should pass (no validation)
        composite.validate("anything", "field")
        composite.validate(None, "field")
        composite.validate(123, "field")


class TestPredefinedValidators:
    """Test predefined validator instances."""

    def test_dns_record_type_validator(self):
        """Test DNS record type validator."""
        # Valid record types
        DNS_RECORD_TYPE_VALIDATOR.validate("A", "record_type")
        DNS_RECORD_TYPE_VALIDATOR.validate("AAAA", "record_type")
        DNS_RECORD_TYPE_VALIDATOR.validate("a", "record_type")  # Case insensitive
        DNS_RECORD_TYPE_VALIDATOR.validate("cname", "record_type")

        # Invalid record type
        with pytest.raises(ValueError, match="record_type must be one of"):
            DNS_RECORD_TYPE_VALIDATOR.validate("INVALID", "record_type")

    def test_health_status_validator(self):
        """Test health status validator."""
        # Valid statuses
        HEALTH_STATUS_VALIDATOR.validate("healthy", "status")
        HEALTH_STATUS_VALIDATOR.validate("DEGRADED", "status")  # Case insensitive
        HEALTH_STATUS_VALIDATOR.validate("unhealthy", "status")

        # Invalid status
        with pytest.raises(ValueError, match="status must be one of"):
            HEALTH_STATUS_VALIDATOR.validate("broken", "status")

    def test_error_severity_validator(self):
        """Test error severity validator."""
        # Valid severities
        ERROR_SEVERITY_VALIDATOR.validate("debug", "severity")
        ERROR_SEVERITY_VALIDATOR.validate("INFO", "severity")  # Case insensitive
        ERROR_SEVERITY_VALIDATOR.validate("critical", "severity")

        # Invalid severity
        with pytest.raises(ValueError, match="severity must be one of"):
            ERROR_SEVERITY_VALIDATOR.validate("urgent", "severity")

    def test_positive_integer_validator(self):
        """Test positive integer validator."""
        POSITIVE_INTEGER_VALIDATOR.validate(1, "count")
        POSITIVE_INTEGER_VALIDATOR.validate(100, "count")

        with pytest.raises(ValueError, match="count must be positive"):
            POSITIVE_INTEGER_VALIDATOR.validate(0, "count")
        with pytest.raises(ValueError, match="count must be positive"):
            POSITIVE_INTEGER_VALIDATOR.validate(-1, "count")
        with pytest.raises(ValueError, match="count must be int"):
            POSITIVE_INTEGER_VALIDATOR.validate(1.5, "count")

    def test_non_negative_integer_validator(self):
        """Test non-negative integer validator."""
        NON_NEGATIVE_INTEGER_VALIDATOR.validate(0, "ttl")
        NON_NEGATIVE_INTEGER_VALIDATOR.validate(3600, "ttl")

        with pytest.raises(ValueError, match="ttl must be at least 0"):
            NON_NEGATIVE_INTEGER_VALIDATOR.validate(-1, "ttl")
        with pytest.raises(ValueError, match="ttl must be int"):
            NON_NEGATIVE_INTEGER_VALIDATOR.validate(3.14, "ttl")

    def test_non_empty_string_validator(self):
        """Test non-empty string validator."""
        NON_EMPTY_STRING_VALIDATOR.validate("test", "name")
        NON_EMPTY_STRING_VALIDATOR.validate("hello world", "name")

        with pytest.raises(ValueError, match="name cannot be empty"):
            NON_EMPTY_STRING_VALIDATOR.validate("", "name")
        with pytest.raises(ValueError, match="name cannot be empty"):
            NON_EMPTY_STRING_VALIDATOR.validate("   ", "name")

    def test_hostname_validator(self):
        """Test hostname validator."""
        # Valid hostnames
        HOSTNAME_VALIDATOR.validate("example.com", "hostname")
        HOSTNAME_VALIDATOR.validate("sub.example.com", "hostname")
        HOSTNAME_VALIDATOR.validate("host", "hostname")
        HOSTNAME_VALIDATOR.validate("my-server.example.org", "hostname")

        # Invalid hostnames
        with pytest.raises(
            ValueError, match="hostname does not match required pattern"
        ):
            HOSTNAME_VALIDATOR.validate("-invalid.com", "hostname")
        with pytest.raises(
            ValueError, match="hostname does not match required pattern"
        ):
            HOSTNAME_VALIDATOR.validate("invalid-.com", "hostname")
        with pytest.raises(ValueError, match="hostname cannot be empty"):
            HOSTNAME_VALIDATOR.validate("", "hostname")

    def test_ipv4_validator(self):
        """Test IPv4-only validator."""
        IPV4_VALIDATOR.validate("192.168.1.1", "ip")
        IPV4_VALIDATOR.validate("10.0.0.1", "ip")

        with pytest.raises(ValueError, match="ip IPv6 addresses are not allowed"):
            IPV4_VALIDATOR.validate("2001:db8::1", "ip")
        with pytest.raises(ValueError, match="ip must be a valid IPv4 address"):
            IPV4_VALIDATOR.validate("not-an-ip", "ip")


class TestValidationMixinInterface:
    """Test ValidationMixin abstract interface."""

    def test_abstract_validation_mixin(self):
        """Test that ValidationMixin cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ValidationMixin()

    def test_custom_validator_implementation(self):
        """Test implementing a custom validator."""

        class CustomValidator(ValidationMixin):
            def validate(self, value, field_name):
                if value != "custom":
                    raise ValueError(f"{field_name} must be 'custom'")

        validator = CustomValidator()
        validator.validate("custom", "field")

        with pytest.raises(ValueError, match="field must be 'custom'"):
            validator.validate("other", "field")


class TestValidationMixinIntegration:
    """Test integration scenarios with validation mixins."""

    def test_field_name_in_error_messages(self):
        """Test that field names appear correctly in error messages."""
        validator = StringValidator(min_length=5)

        with pytest.raises(ValueError, match="username must be at least 5 characters"):
            validator.validate("hi", "username")

        with pytest.raises(ValueError, match="password must be at least 5 characters"):
            validator.validate("abc", "password")

    def test_complex_validation_scenario(self):
        """Test a complex validation scenario."""
        # Create a validator for DNS record names
        dns_name_validator = CompositeValidator(
            [
                StringValidator(
                    allow_empty=False,
                    max_length=253,
                    pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$",
                )
            ]
        )

        # Valid DNS names
        dns_name_validator.validate("example.com", "dns_name")
        dns_name_validator.validate("sub.example.com", "dns_name")
        dns_name_validator.validate("my-server.example.org", "dns_name")

        # Invalid DNS names
        with pytest.raises(ValueError):
            dns_name_validator.validate("", "dns_name")
        with pytest.raises(ValueError):
            dns_name_validator.validate("-invalid.com", "dns_name")

    def test_validation_with_type_conversion(self):
        """Test validation behavior with type conversion scenarios."""
        # Numeric validator should handle actual numbers, not strings
        validator = NumericValidator(min_value=0, max_value=100)

        validator.validate(50, "percentage")
        validator.validate(0, "percentage")
        validator.validate(100, "percentage")

        # Should reject string numbers (no automatic conversion)
        with pytest.raises(ValueError, match="percentage must be int or float"):
            validator.validate("50", "percentage")
