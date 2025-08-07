"""
Edge case and error handling tests for *_event.py classes in app/joyride/events/types/
"""
import pytest

from app.joyride.events.types import (
    container_event,
    dns_event,
    error_event,
    file_event,
    health_event,
    node_event,
    system_event,
)


def test_system_event_validation_errors():
    # Missing component
    with pytest.raises(ValueError):
        system_event.SystemEvent(
            event_type="system.test",
            source="test",
            component="",
            operation="start",
            status="success"
        )._validate()
    # Missing operation
    with pytest.raises(ValueError):
        system_event.SystemEvent(
            event_type="system.test",
            source="test",
            component="core",
            operation="",
            status="success"
        )._validate()
    # Missing status
    with pytest.raises(ValueError):
        system_event.SystemEvent(
            event_type="system.test",
            source="test",
            component="core",
            operation="start",
            status=""
        )._validate()

  
def test_node_event_validation_errors():
    with pytest.raises(ValueError):
        node_event.NodeEvent(
            event_type="node.test",
            source="test",
            node_id="",
            node_address="127.0.0.1",
            node_port=5353,
            node_state="active"
        )._validate()
    with pytest.raises(ValueError):
        node_event.NodeEvent(
            event_type="node.test",
            source="test",
            node_id="node1",
            node_address="127.0.0.1",
            node_port=5353,
            node_state=""
        )._validate()

  
def test_health_event_validation_errors():
    with pytest.raises(ValueError):
        health_event.HealthEvent(
            event_type="health.test",
            source="test",
            component="",
            health_status="healthy",
            check_name="ping",
            check_result=True
        )._validate()
    with pytest.raises(ValueError):
        health_event.HealthEvent(
            event_type="health.test",
            source="test",
            component="core",
            health_status="",
            check_name="ping",
            check_result=True
        )._validate()

  
def test_file_event_validation_errors():
    with pytest.raises(ValueError):
        file_event.FileEvent(
            event_type="file.test",
            source="test",
            file_path="",
            operation="modified"
        )._validate()
    with pytest.raises(ValueError):
        file_event.FileEvent(
            event_type="file.test",
            source="test",
            file_path="/tmp/test",
            operation=""
        )._validate()

  
def test_error_event_validation_errors():
    with pytest.raises(ValueError):
        error_event.ErrorEvent(
            event_type="error.test",
            source="test",
            error_code="",
            error_type="runtime",
            error_message="fail",
            severity="high"
        )._validate()
    with pytest.raises(ValueError):
        error_event.ErrorEvent(
            event_type="error.test",
            source="test",
            error_code="E001",
            error_type="runtime",
            error_message="fail",
            severity=""
        )._validate()

  
def test_dns_event_validation_errors():
    with pytest.raises(ValueError):
        dns_event.DNSEvent(
            event_type="dns.test",
            source="test",
            record_type="",
            record_name="test.internal"
        )._validate()
    with pytest.raises(ValueError):
        dns_event.DNSEvent(
            event_type="dns.test",
            source="test",
            record_type="A",
            record_name=""
        )._validate()

  
def test_container_event_validation_errors():
    try:
        event = container_event.ContainerEvent(
            event_type="container.test",
            source="test",
            container_id="",
            container_name="test",
            image="alpine",
            status="running"
        )
        print(f"container_id: '{event.container_id}'")
        event._validate()
    except ValueError as e:
        print(f"Caught ValueError: {e}")
        return
    assert False, "Expected ValueError for empty container_id"
    with pytest.raises(ValueError):
        container_event.ContainerEvent(
            event_type="container.test",
            source="test",
            container_id="abc123",
            container_name="test",
            image="alpine",
            status=""
        )._validate()
