"""
Tests for the event factory system.

This module tests the EventFactory class and its ability to create
events consistently using the schema composition system.
"""

import pytest
from datetime import datetime

from app.joyride.events.event_factory import EventFactory
from app.joyride.events.types import (
    ContainerEvent,
    DNSEvent,
    ErrorEvent,
    FileEvent,
    HealthEvent,
    NodeEvent,
    SystemEvent,
)


class TestEventFactory:
    """Test the EventFactory class."""
    
    def test_create_event_container(self):
        """Test creating a container event using the factory."""
        event = EventFactory.create_event(
            event_category='container',
            event_type='container_started',
            source='docker_monitor',
            container_id='abc123',
            container_name='web-server',
            image='nginx:latest',
            status='running'
        )
        
        assert isinstance(event, ContainerEvent)
        assert event.event_type == 'container_started'
        assert event.source == 'docker_monitor'
        assert event.container_id == 'abc123'
        assert event.container_name == 'web-server'
        assert event.image == 'nginx:latest'
        assert event.status == 'running'
        assert isinstance(event.timestamp, datetime)
    
    def test_create_event_dns(self):
        """Test creating a DNS event using the factory."""
        event = EventFactory.create_event(
            event_category='dns',
            event_type='record_added',
            source='dns_handler',
            record_name='example.com',
            record_type='A',
            record_value='192.168.1.100',
            ttl=300
        )
        
        assert isinstance(event, DNSEvent)
        assert event.event_type == 'record_added'
        assert event.source == 'dns_handler'
        assert event.record_name == 'example.com'
        assert event.record_type == 'A'
        assert event.record_value == '192.168.1.100'
        assert event.ttl == 300
    
    def test_create_event_error(self):
        """Test creating an error event using the factory."""
        event = EventFactory.create_event(
            event_category='error',
            event_type='validation_failed',
            source='validator',
            error_message='Invalid hostname format',
            error_code='INVALID_HOSTNAME',
            severity='error'
        )
        
        assert isinstance(event, ErrorEvent)
        assert event.event_type == 'validation_failed'
        assert event.source == 'validator'
        assert event.error_message == 'Invalid hostname format'
        assert event.error_code == 'INVALID_HOSTNAME'
        assert event.severity == 'error'
    
    def test_create_event_file(self):
        """Test creating a file event using the factory."""
        event = EventFactory.create_event(
            event_category='file',
            event_type='file_modified',
            source='file_watcher',
            file_path='/etc/hosts',
            operation='write'
        )
        
        assert isinstance(event, FileEvent)
        assert event.event_type == 'file_modified'
        assert event.source == 'file_watcher'
        assert event.file_path == '/etc/hosts'
        assert event.operation == 'write'
    
    def test_create_event_health(self):
        """Test creating a health event using the factory."""
        event = EventFactory.create_event(
            event_category='health',
            event_type='check_passed',
            source='health_monitor',
            component='dns_server',
            status='healthy',
            check_name='port_availability'
        )
        
        assert isinstance(event, HealthEvent)
        assert event.event_type == 'check_passed'
        assert event.source == 'health_monitor'
        assert event.component == 'dns_server'
        assert event.health_status == 'healthy'
        assert event.check_name == 'port_availability'
    
    def test_create_event_node(self):
        """Test creating a node event using the factory."""
        event = EventFactory.create_event(
            event_category='node',
            event_type='node_added',
            source='cluster_manager',
            node_id='node-001',
            node_address='192.168.1.100',
            node_port=8080,
            node_state='active'
        )
        
        assert isinstance(event, NodeEvent)
        assert event.event_type == 'node_added'
        assert event.source == 'cluster_manager'
        assert event.node_id == 'node-001'
        assert event.node_address == '192.168.1.100'
        assert event.node_port == 8080
        assert event.node_state == 'active'
    
    def test_create_event_system(self):
        """Test creating a system event using the factory."""
        event = EventFactory.create_event(
            event_category='system',
            event_type='service_started',
            source='system_monitor',
            component='dns_server',
            operation='start',
            status='success'
        )
        
        assert isinstance(event, SystemEvent)
        assert event.event_type == 'service_started'
        assert event.source == 'system_monitor'
        assert event.component == 'dns_server'
        assert event.operation == 'start'
        assert event.status == 'success'
    
    def test_create_event_validation_failure(self):
        """Test error handling for validation failures."""
        with pytest.raises(ValueError, match="DNS record name cannot be empty"):
            EventFactory.create_event(
                event_category='dns',
                event_type='record_added',
                source='test',
                # Missing required record_name
                record_type='A'
            )


class TestEventFactoryConvenienceMethods:
    """Test the convenience methods of EventFactory."""
    
    def test_create_health_event(self):
        """Test the create_health_event convenience method."""
        event = EventFactory.create_health_event(
            event_type='check_passed',
            source='health_monitor',
            component='dns_server',
            health_status='healthy'
        )
        
        assert isinstance(event, HealthEvent)
        assert event.component == 'dns_server'
        assert event.health_status == 'healthy'
    
    def test_create_node_event(self):
        """Test the create_node_event convenience method."""
        event = EventFactory.create_node_event(
            event_type='node_joined',
            source='swim_protocol',
            node_id='node-001',
            node_address='192.168.1.10',
            node_port=7946,
            node_state='alive'
        )
        
        assert isinstance(event, NodeEvent)
        assert event.node_id == 'node-001'
        assert event.node_state == 'alive'
    
    def test_create_system_event(self):
        """Test the create_system_event convenience method."""
        event = EventFactory.create_system_event(
            event_type='service_started',
            source='orchestrator',
            component='dns_server',
            operation='start'
        )
        
        assert isinstance(event, SystemEvent)
        assert event.component == 'dns_server'
        assert event.operation == 'start'
