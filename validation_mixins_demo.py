"""
Example demonstrating how validation mixins replace repetitive validation code.

This file shows the "before" and "after" for how validation mixins eliminate
repetitive validation code in event classes.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.joyride.events import Event
from app.joyride.events.validation_mixins import (
    DNS_RECORD_TYPE_VALIDATOR,
    NON_EMPTY_STRING_VALIDATOR,
    NON_NEGATIVE_INTEGER_VALIDATOR,
    ChoiceValidator,
    CompositeValidator,
    NumericValidator,
    StringValidator,
)


# BEFORE: Repetitive validation code in each event type
class DNSEventBefore(Event):
    """DNS event before validation mixins - shows repetitive validation."""

    def __init__(
        self,
        event_type: str,
        source: str,
        record_name: str,
        record_type: str,
        record_value: Optional[str] = None,
        ttl: int = 3600,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        event_data = data or {}
        event_data.update({
            "record_name": record_name,
            "record_type": record_type,
            "record_value": record_value,
            "ttl": ttl,
        })

        super().__init__(
            event_type=event_type,
            source=source,
            data=event_data,
            metadata=metadata,
            timestamp=timestamp,
        )

    def _validate(self) -> None:
        """Validate DNS event data - REPETITIVE VALIDATION CODE."""
        super()._validate()

        # Repetitive string empty checks
        if not self.data["record_name"]:
            raise ValueError("DNS record name cannot be empty")

        if not self.data["record_type"]:
            raise ValueError("DNS record type cannot be empty")

        # Repetitive numeric validation
        if self.data["ttl"] < 0:
            raise ValueError("DNS record TTL must be non-negative")

        # Repetitive choice validation
        valid_types = ["A", "AAAA", "CNAME", "MX", "NS", "PTR", "SOA", "SRV", "TXT"]
        if self.data["record_type"].upper() not in valid_types:
            raise ValueError(f"DNS record type must be one of: {', '.join(valid_types)}")


# AFTER: Using validation mixins - clean and reusable
class DNSEventAfter(Event):
    """DNS event after validation mixins - clean validation."""

    # Define validators once - reusable across all DNS events
    _validators = {
        "record_name": NON_EMPTY_STRING_VALIDATOR,
        "record_type": DNS_RECORD_TYPE_VALIDATOR,
        "ttl": NON_NEGATIVE_INTEGER_VALIDATOR,
    }

    def __init__(
        self,
        event_type: str,
        source: str,
        record_name: str,
        record_type: str,
        record_value: Optional[str] = None,
        ttl: int = 3600,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        event_data = data or {}
        event_data.update({
            "record_name": record_name,
            "record_type": record_type,
            "record_value": record_value,
            "ttl": ttl,
        })

        super().__init__(
            event_type=event_type,
            source=source,
            data=event_data,
            metadata=metadata,
            timestamp=timestamp,
        )

    def _validate(self) -> None:
        """Validate DNS event data - CLEAN VALIDATION WITH MIXINS."""
        super()._validate()

        # Apply validators - no repetitive code!
        for field_name, validator in self._validators.items():
            if field_name in self.data:
                validator.validate(self.data[field_name], field_name)


# Another example showing complex validation composition
class AdvancedDNSEvent(Event):
    """Advanced DNS event showing composite validation."""

    # Complex validation can be composed from simpler validators
    _advanced_validators = {
        "hostname": CompositeValidator([
            StringValidator(
                allow_empty=False,
                max_length=253,
                pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
            )
        ]),
        "priority": NumericValidator(
            numeric_type=int,
            min_value=0,
            max_value=65535
        ),
        "status": ChoiceValidator(
            choices=["active", "inactive", "pending"],
            case_sensitive=False
        ),
    }

    def __init__(
        self,
        event_type: str,
        source: str,
        hostname: str,
        priority: int,
        status: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        event_data = data or {}
        event_data.update({
            "hostname": hostname,
            "priority": priority,
            "status": status,
        })

        super().__init__(
            event_type=event_type,
            source=source,
            data=event_data,
            metadata=metadata,
            timestamp=timestamp,
        )

    def _validate(self) -> None:
        """Advanced validation with composed validators."""
        super()._validate()

        # Same simple loop handles complex validation
        for field_name, validator in self._advanced_validators.items():
            if field_name in self.data:
                validator.validate(self.data[field_name], field_name)


def demonstrate_validation_mixins():
    """Demonstrate validation mixins in action."""
    print("=== Validation Mixins Demonstration ===\\n")

    # Test valid DNS event
    try:
        DNSEventAfter(
            event_type="dns.record.added",
            source="dns-server",
            record_name="example.com",
            record_type="A",
            record_value="192.168.1.1",
            ttl=3600
        )
        print("✓ Valid DNS event created successfully")
    except ValueError as e:
        print(f"✗ Unexpected validation error: {e}")

    # Test validation errors
    test_cases = [
        # Empty record name
        {
            "record_name": "",
            "record_type": "A",
            "ttl": 3600,
            "expected_error": "record_name cannot be empty"
        },
        # Invalid record type
        {
            "record_name": "example.com",
            "record_type": "INVALID",
            "ttl": 3600,
            "expected_error": "record_type must be one of"
        },
        # Negative TTL
        {
            "record_name": "example.com",
            "record_type": "A",
            "ttl": -1,
            "expected_error": "ttl must be at least 0"
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        try:
            DNSEventAfter(
                event_type="dns.record.added",
                source="dns-server",
                record_name=test_case["record_name"],
                record_type=test_case["record_type"],
                ttl=test_case["ttl"]
            )
            print(f"✗ Test {i}: Expected validation error but none occurred")
        except ValueError as e:
            if test_case["expected_error"] in str(e):
                print(f"✓ Test {i}: Validation correctly caught: {e}")
            else:
                print(f"✗ Test {i}: Unexpected error message: {e}")

    print("\\n=== Advanced Validation Demonstration ===\\n")

    # Test advanced validation
    try:
        AdvancedDNSEvent(
            event_type="dns.advanced",
            source="dns-manager",
            hostname="valid-host.example.com",
            priority=100,
            status="active"
        )
        print("✓ Advanced DNS event created successfully")
    except ValueError as e:
        print(f"✗ Unexpected advanced validation error: {e}")

    # Test advanced validation errors
    advanced_test_cases = [
        # Invalid hostname
        {
            "hostname": "-invalid.com",
            "priority": 100,
            "status": "active",
            "expected_error": "hostname does not match required pattern"
        },
        # Invalid priority
        {
            "hostname": "valid.com",
            "priority": 70000,  # Too high
            "status": "active",
            "expected_error": "priority must be at most 65535"
        },
        # Invalid status
        {
            "hostname": "valid.com",
            "priority": 100,
            "status": "unknown",
            "expected_error": "status must be one of"
        },
    ]

    for i, test_case in enumerate(advanced_test_cases, 1):
        try:
            AdvancedDNSEvent(
                event_type="dns.advanced",
                source="dns-manager",
                hostname=test_case["hostname"],
                priority=test_case["priority"],
                status=test_case["status"]
            )
            print(f"✗ Advanced Test {i}: Expected validation error but none occurred")
        except ValueError as e:
            if test_case["expected_error"] in str(e):
                print(f"✓ Advanced Test {i}: Validation correctly caught: {e}")
            else:
                print(f"✗ Advanced Test {i}: Unexpected error message: {e}")

    print("\\n=== Benefits Summary ===")
    print("1. ✓ Eliminated repetitive validation code")
    print("2. ✓ Reusable validators across event types")
    print("3. ✓ Composable validation logic")
    print("4. ✓ Consistent error messages")
    print("5. ✓ Easy to test and maintain")
    print("6. ✓ Declarative validation definitions")


if __name__ == "__main__":
    demonstrate_validation_mixins()
