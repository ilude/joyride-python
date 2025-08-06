"""
Tests for event schema composition system.

Tests the EventSchema class and related utilities for declarative event definitions,
schema validation, and data handling.
"""

import pytest

from app.joyride.events.event_schemas import (
    EventSchema,
    SchemaFactory,
    SchemaField,
    SchemaValidator,
)
from app.joyride.events.fields import IntField, StringField
from app.joyride.events.schemas import (
    ContainerEventSchema,
    DNSEventSchema,
    ErrorEventSchema,
    FileEventSchema,
    HealthEventSchema,
    NodeEventSchema,
    SystemEventSchema,
)


class TestEventSchema:
    """Test EventSchema base functionality."""
    
    def test_schema_creation_empty(self):
        """Test creating an empty schema."""
        class EmptySchema(EventSchema):
            pass
        
        schema = EmptySchema()
        assert schema.to_dict() == {}
        assert schema.is_valid is True
        assert schema.errors == {}
    
    def test_schema_with_fields(self):
        """Test schema with field definitions."""
        class TestSchema(EventSchema):
            name = StringField(data_key="name")
            count = IntField(data_key="count", default=0)
        
        # Test with required field
        schema = TestSchema(name="test", count=5)
        assert schema.name == "test"
        assert schema.count == 5
        assert schema.to_dict() == {"name": "test", "count": 5}
        assert schema.is_valid is True
    
    def test_schema_missing_required_field(self):
        """Test schema validation with missing required field."""
        class TestSchema(EventSchema):
            name = StringField(data_key="name")
            count = IntField(data_key="count", default=0)
        
        with pytest.raises(ValueError, match="Required field 'name' is missing"):
            TestSchema(count=5)
    
    def test_schema_default_values(self):
        """Test schema with default values."""
        class TestSchema(EventSchema):
            name = StringField(data_key="name", default="default")
            count = IntField(data_key="count", default=42)
        
        schema = TestSchema()
        assert schema.name == "default"
        assert schema.count == 42
        assert schema.to_dict() == {"name": "default", "count": 42}
    
    def test_schema_attribute_access(self):
        """Test attribute-style access to schema data."""
        class TestSchema(EventSchema):
            name = StringField(data_key="name")
        
        schema = TestSchema(name="test")
        assert schema.name == "test"
        
        # Test setting attributes
        schema.name = "updated"
        assert schema.name == "updated"
        assert schema.to_dict()["name"] == "updated"
    
    def test_schema_extra_fields(self):
        """Test schema handling of extra fields not in definition."""
        class TestSchema(EventSchema):
            name = StringField(data_key="name")
        
        schema = TestSchema(name="test", extra="value")
        assert schema.name == "test"
        assert schema.extra == "value"
        assert schema.to_dict() == {"name": "test", "extra": "value"}
    
    def test_schema_validation_method(self):
        """Test explicit validation method."""
        class TestSchema(EventSchema):
            name = StringField(data_key="name")
            count = IntField(data_key="count", default=0)
        
        schema = TestSchema(name="test")
        assert schema.validate() is True
        assert schema.is_valid is True
        assert schema.errors == {}
    
    def test_schema_field_info(self):
        """Test schema introspection methods."""
        class TestSchema(EventSchema):
            name = StringField(data_key="name")
            count = IntField(data_key="count", default=0)
        
        field_names = TestSchema.get_field_names()
        assert "name" in field_names
        assert "count" in field_names
        
        required_fields = TestSchema.get_required_fields()
        assert "name" in required_fields
        assert "count" not in required_fields  # Has default value
        
        field_info = TestSchema.get_field_info("name")
        assert field_info is not None
        assert field_info.name == "name"
        assert field_info.required is True


class TestSchemaField:
    """Test SchemaField functionality."""
    
    def test_schema_field_creation(self):
        """Test creating a SchemaField."""
        field_desc = StringField(data_key="test")
        schema_field = SchemaField(
            name="test",
            field_descriptor=field_desc,
            required=True
        )
        
        assert schema_field.name == "test"
        assert schema_field.field_descriptor == field_desc
        assert schema_field.required is True
        assert schema_field.default is None
    
    def test_schema_field_with_default(self):
        """Test SchemaField with default value."""
        field_desc = StringField(data_key="test", default="default")
        schema_field = SchemaField(
            name="test",
            field_descriptor=field_desc,
            default="default"
        )
        
        assert schema_field.default == "default"
        assert schema_field.required is True  # Still required even with default


class TestSchemaFactory:
    """Test SchemaFactory for dynamic schema creation."""
    
    def test_create_simple_schema(self):
        """Test creating a schema dynamically."""
        fields = {
            "name": StringField(data_key="name"),
            "count": IntField(data_key="count", default=0)
        }
        
        TestSchema = SchemaFactory.create_schema("TestSchema", fields)
        assert issubclass(TestSchema, EventSchema)
        
        # Test using the created schema
        schema = TestSchema(name="test")
        assert schema.name == "test"
        assert schema.count == 0
    
    def test_create_schema_with_base_classes(self):
        """Test creating schema with custom base classes."""
        class BaseSchema(EventSchema):
            base_field = StringField(data_key="base", default="base")
        
        fields = {
            "name": StringField(data_key="name")
        }
        
        TestSchema = SchemaFactory.create_schema(
            "TestSchema", fields, base_classes=(BaseSchema,)
        )
        
        schema = TestSchema(name="test")
        assert schema.name == "test"
        assert schema.base_field == "base"
    
    def test_create_schema_invalid_field(self):
        """Test error handling for invalid field definitions."""
        fields = {
            "invalid": "not_a_field"
        }
        
        with pytest.raises(ValueError, match="Invalid field definition"):
            SchemaFactory.create_schema("TestSchema", fields)


class TestSchemaValidator:
    """Test SchemaValidator utilities."""
    
    def test_validate_data_success(self):
        """Test successful data validation."""
        class TestSchema(EventSchema):
            name = StringField(data_key="name")
            count = IntField(data_key="count", default=0)
        
        data = {"name": "test", "count": 5}
        is_valid, validated_data, errors = SchemaValidator.validate_data(TestSchema, data)
        
        assert is_valid is True
        assert validated_data == data
        assert errors == {}
    
    def test_validate_data_failure(self):
        """Test data validation failure."""
        class TestSchema(EventSchema):
            name = StringField(data_key="name")
        
        data = {"count": 5}  # Missing required 'name'
        is_valid, validated_data, errors = SchemaValidator.validate_data(TestSchema, data)
        
        assert is_valid is False
        assert validated_data == {}
        assert "validation_error" in errors
    
    def test_merge_schemas(self):
        """Test merging two schemas."""
        class Schema1(EventSchema):
            field1 = StringField(data_key="field1")
        
        class Schema2(EventSchema):
            field2 = IntField(data_key="field2", default=0)
        
        MergedSchema = SchemaValidator.merge_schemas(Schema1, Schema2, "MergedSchema")
        
        # Test that merged schema has fields from both schemas
        field_names = MergedSchema.get_field_names()
        assert "field1" in field_names
        assert "field2" in field_names
        
        # Test using the merged schema
        schema = MergedSchema(field1="test")
        assert schema.field1 == "test"
        assert schema.field2 == 0


class TestContainerEventSchema:
    """Test ContainerEventSchema."""
    
    def test_container_schema_creation(self):
        """Test creating a container event schema."""
        data = {
            "container_id": "abc123",
            "container_name": "test-container",
            "event_type": "started",
            "timestamp": 1609459200
        }
        
        schema = ContainerEventSchema(**data)
        assert schema.container_id == "abc123"
        assert schema.container_name == "test-container"
        assert schema.event_type == "started"
        assert schema.timestamp == 1609459200
        assert schema.is_valid is True
    
    def test_container_schema_defaults(self):
        """Test container schema with default values."""
        data = {
            "container_id": "abc123",
            "container_name": "test-container",
            "event_type": "started",
            "timestamp": 1609459200
        }
        
        schema = ContainerEventSchema(**data)
        assert schema.image == ""
        assert schema.labels == {}
        assert schema.hostname == ""
        assert schema.domain_suffix == ".internal"
    
    def test_container_schema_missing_required(self):
        """Test container schema with missing required fields."""
        data = {
            "container_name": "test-container",
            "event_type": "started",
            "timestamp": 1609459200
        }
        
        with pytest.raises(ValueError, match="Required field 'container_id' is missing"):
            ContainerEventSchema(**data)


class TestDNSEventSchema:
    """Test DNSEventSchema."""
    
    def test_dns_schema_creation(self):
        """Test creating a DNS event schema."""
        data = {
            "hostname": "test.example.com",
            "record_type": "A",
            "event_type": "added",
            "timestamp": 1609459200,
            "ip_address": "192.168.1.100",
            "source": "container"
        }
        
        schema = DNSEventSchema(**data)
        assert schema.hostname == "test.example.com"
        assert schema.record_type == "A"
        assert schema.event_type == "added"
        assert schema.ip_address == "192.168.1.100"
        assert schema.source == "container"
        assert schema.is_valid is True
    
    def test_dns_schema_defaults(self):
        """Test DNS schema with default values."""
        data = {
            "hostname": "test.example.com",
            "record_type": "A",
            "event_type": "added",
            "timestamp": 1609459200,
            "ip_address": "192.168.1.100",
            "source": "container"
        }
        
        schema = DNSEventSchema(**data)
        assert schema.ttl == 300
        assert schema.source_id == ""
        assert schema.priority == 0


class TestFileEventSchema:
    """Test FileEventSchema."""
    
    def test_file_schema_creation(self):
        """Test creating a file event schema."""
        data = {
            "file_path": "/etc/hosts",
            "file_name": "hosts",
            "event_type": "modified",
            "timestamp": 1609459200
        }
        
        schema = FileEventSchema(**data)
        assert schema.file_path == "/etc/hosts"
        assert schema.file_name == "hosts"
        assert schema.event_type == "modified"
        assert schema.timestamp == 1609459200
        assert schema.is_valid is True
    
    def test_file_schema_defaults(self):
        """Test file schema with default values."""
        data = {
            "file_path": "/etc/hosts",
            "file_name": "hosts",
            "event_type": "modified",
            "timestamp": 1609459200
        }
        
        schema = FileEventSchema(**data)
        assert schema.file_size == 0
        assert schema.last_modified == 0
        assert schema.total_records == 0


class TestNodeEventSchema:
    """Test NodeEventSchema."""
    
    def test_node_schema_creation(self):
        """Test creating a node event schema."""
        data = {
            "node_id": "node-001",
            "node_address": "192.168.1.10",
            "node_port": 8080,
            "event_type": "joined",
            "timestamp": 1609459200
        }
        
        schema = NodeEventSchema(**data)
        assert schema.node_id == "node-001"
        assert schema.node_address == "192.168.1.10"
        assert schema.node_port == 8080
        assert schema.event_type == "joined"
        assert schema.timestamp == 1609459200
        assert schema.is_valid is True
    
    def test_node_schema_defaults(self):
        """Test node schema with default values."""
        data = {
            "node_id": "node-001",
            "node_address": "192.168.1.10",
            "node_port": 8080,
            "event_type": "joined",
            "timestamp": 1609459200
        }
        
        schema = NodeEventSchema(**data)
        assert schema.node_name == ""
        assert schema.version == ""
        assert schema.incarnation == 0
        assert schema.cluster_size == 1


class TestSystemEventSchema:
    """Test SystemEventSchema."""
    
    def test_system_schema_creation(self):
        """Test creating a system event schema."""
        data = {
            "event_type": "startup",
            "timestamp": 1609459200,
            "component": "dns_server",
            "severity": "info",
            "message": "DNS server starting"
        }
        
        schema = SystemEventSchema(**data)
        assert schema.event_type == "startup"
        assert schema.timestamp == 1609459200
        assert schema.component == "dns_server"
        assert schema.severity == "info"
        assert schema.message == "DNS server starting"
        assert schema.is_valid is True
    
    def test_system_schema_defaults(self):
        """Test system schema with default values."""
        data = {
            "event_type": "startup",
            "timestamp": 1609459200,
            "component": "dns_server",
            "severity": "info",
            "message": "DNS server starting"
        }
        
        schema = SystemEventSchema(**data)
        assert schema.component_version == ""
        assert schema.process_id == 0
        assert schema.thread_id == 0
        assert schema.memory_usage == 0
        assert schema.metadata == {}


class TestErrorEventSchema:
    """Test ErrorEventSchema."""
    
    def test_error_schema_creation(self):
        """Test creating an error event schema."""
        data = {
            "error_code": "DNS001",
            "error_type": "DNSResolutionError",
            "timestamp": 1609459200,
            "message": "Failed to resolve hostname",
            "severity": "high",
            "component": "dns_server"
        }
        
        schema = ErrorEventSchema(**data)
        assert schema.error_code == "DNS001"
        assert schema.error_type == "DNSResolutionError"
        assert schema.message == "Failed to resolve hostname"
        assert schema.severity == "high"
        assert schema.component == "dns_server"
        assert schema.is_valid is True
    
    def test_error_schema_defaults(self):
        """Test error schema with default values."""
        data = {
            "error_code": "DNS001",
            "error_type": "DNSResolutionError",
            "timestamp": 1609459200,
            "message": "Failed to resolve hostname",
            "severity": "high",
            "component": "dns_server"
        }
        
        schema = ErrorEventSchema(**data)
        assert schema.operation == ""
        assert schema.stack_trace == ""
        assert schema.context == {}
        assert schema.retry_count == 0


class TestHealthEventSchema:
    """Test HealthEventSchema."""
    
    def test_health_schema_creation(self):
        """Test creating a health event schema."""
        data = {
            "check_name": "dns_resolution",
            "component": "dns_server",
            "timestamp": 1609459200,
            "status": "healthy",
            "check_duration": 50
        }
        
        schema = HealthEventSchema(**data)
        assert schema.check_name == "dns_resolution"
        assert schema.component == "dns_server"
        assert schema.status == "healthy"
        assert schema.check_duration == 50
        assert schema.is_valid is True
    
    def test_health_schema_defaults(self):
        """Test health schema with default values."""
        data = {
            "check_name": "dns_resolution",
            "component": "dns_server",
            "timestamp": 1609459200,
            "status": "healthy",
            "check_duration": 50
        }
        
        schema = HealthEventSchema(**data)
        assert schema.previous_status == "unknown"
        assert schema.response_time == 0
        assert schema.metrics == {}
        assert schema.thresholds == {}
        assert schema.message == ""
        assert schema.details == {}


class TestSchemaIntegration:
    """Test schema integration with existing event system."""
    
    def test_schema_to_dict_integration(self):
        """Test schema to_dict method for event creation."""
        schema = ContainerEventSchema(
            container_id="abc123",
            container_name="test-container",
            event_type="started",
            timestamp=1609459200,
            image="nginx:latest",
            hostname="test"
        )
        
        data = schema.to_dict()
        expected_keys = {
            "container_id", "container_name", "event_type", "timestamp",
            "image", "labels", "hostname", "domain_suffix"
        }
        
        assert set(data.keys()) == expected_keys
        assert data["container_id"] == "abc123"
        assert data["image"] == "nginx:latest"
        assert data["hostname"] == "test"
    
    def test_schema_field_validation_integration(self):
        """Test integration with existing validation system."""
        # Test that schema validation works with field descriptors
        data = {
            "container_id": "abc123",
            "container_name": "test-container",
            "event_type": "started",
            "timestamp": 1609459200
        }
        
        schema = ContainerEventSchema(**data)
        assert schema.validate() is True
        
        # Test field access through descriptors
        assert hasattr(schema, "container_id")
        assert hasattr(schema, "container_name")
        assert hasattr(schema, "event_type")
        assert hasattr(schema, "timestamp")
