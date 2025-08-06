# Event Coordinator Refactor Plan

## Overview

This document outlines a comprehensive refactor to transform the Joyride DNS Service from a tightly coupled architecture to a loosely coupled, event-driven system using SOLID principles, inversion of control, and proven design patterns.

## Current Architecture Analysis

### Existing Structure
```
app/main.py                 # Central orchestrator with tight coupling
├── dns_server.py          # DNS server component
├── dns_sync_manager.py    # SWIM protocol sync
├── docker_monitor.py      # Docker event monitoring  
├── hosts_monitor.py       # Hosts file monitoring
└── [callback-based coupling]
```

### Current Implementation Status (Updated August 2025)

**✅ COMPLETED:**
1. **Event System Foundation** - Fully implemented in `app/joyride/events/`
   - Event base classes with proper naming (Event, not JoyrideEvent)
   - Event types: ContainerEvent, DNSEvent, FileEvent, NodeEvent, SystemEvent, ErrorEvent, HealthEvent
   - EventBus, EventRegistry, EventHandler, EventProducer abstractions
   - Thread-safe event distribution and subscription management

2. **Dependency Injection System** - Fully implemented in `app/joyride/injection/`
   - Provider pattern with multiple lifecycle types (Singleton, Factory, Prototype, Class)
   - Configuration management with hierarchical loading
   - Component lifecycle management with health monitoring
   - Circular dependency detection and resolution

**🚧 PARTIALLY IMPLEMENTED:**
1. **Event Producers** - Need to be created using ENUMs for lifecycle events
2. **Event Handlers** - Need concrete implementations
3. **Integration** - Event system exists but not integrated with existing services

**❌ NAMING CONVENTION ISSUES IDENTIFIED:**
- Current code uses generic names (Event, EventHandler) instead of Joyride-prefixed names
- This conflicts with Python coding standards requiring unique, descriptive names
- Some test files are in `tests/disabled/` indicating incomplete implementation

### Current Problems
1. **Tight Coupling**: Direct callback dependencies between components
2. **Circular Dependencies**: Already experienced with DNS sync callbacks
3. **Monolithic Initialization**: All services initialized in main.py
4. **Hard-coded Dependencies**: Services directly reference each other
5. **Testing Complexity**: Difficult to test components in isolation
6. **Extension Difficulty**: Adding new event sources/handlers requires code changes

### Python Coding Standards Compliance Issues Identified
1. **Naming Convention Violations**: 
   - Current event system uses generic names (Event, EventHandler) instead of descriptive, project-specific names
   - Violates Python instruction: "Use descriptive names" and "Avoid Test Name Conflicts"
   - Should use domain-specific naming like JoyrideEvent, JoyrideEventHandler

2. **Type Safety Issues**:
   - Missing comprehensive type hints in some legacy components
   - Need Pydantic models for structured data validation
   - Event data should use Pydantic models instead of plain dictionaries

3. **Documentation Gaps**:
   - Some modules lack proper docstrings following PEP 257
   - Missing function-level documentation for complex business logic

4. **Code Quality Violations**:
   - Some test files are disabled, indicating incomplete implementation
   - Need to apply Black formatting and isort consistently across all files

## Target Architecture: Event Coordinator Pattern

### Core Design Principles

#### SOLID Principles Application
- **Single Responsibility**: Each component has one clear purpose
- **Open/Closed**: Open for extension (new events/handlers), closed for modification
- **Liskov Substitution**: Event producers/consumers are interchangeable
- **Interface Segregation**: Minimal, focused interfaces
- **Dependency Inversion**: Depend on abstractions, not concrete implementations

#### Design Patterns
- **Observer Pattern**: Event subscription and notification
- **Mediator Pattern**: Central event coordination
- **Strategy Pattern**: Pluggable event handlers
- **Factory Pattern**: Component creation and injection
- **Command Pattern**: Encapsulated event actions

### New Architecture Overview

```
EventCoordinator (Central Hub)
├── Event Producers (Sources)
│   ├── DockerEventProducer     # Docker container events
│   ├── SwimEventProducer       # SWIM protocol events  
│   └── HostsFileEventProducer  # Host file changes
├── Event Handlers (Consumers)
│   ├── DNSRecordHandler        # DNS record management
│   ├── SyncHandler             # DNS sync operations
│   └── LoggingHandler          # Event logging
└── Dependency Injection System
    ├── Configuration           # Environment-based config
    ├── Component Factory       # Service creation
    └── Lifecycle Management    # Start/stop coordination
```

## Detailed Refactor Plan

### Phase 1: Foundation - Event System Infrastructure

#### 1.1 Event System Core
**File Structure:**
```
app/joyride/events/                    # ✅ IMPLEMENTED
├── __init__.py                        # ✅ Event system exports
├── event.py                           # ✅ Event base class  
├── event_bus.py                       # ✅ EventBus implementation
├── event_handler.py                   # ✅ Handler interface
├── event_producer.py                  # ✅ Producer interface
├── event_registry.py                 # ✅ Registry with subscriptions
├── event_filter.py                   # ✅ Event filtering
├── event_subscription.py             # ✅ Subscription management
└── types/                             # ✅ Event type definitions
    ├── __init__.py
    ├── container_event.py             # ✅ Docker container events
    ├── dns_event.py                   # ✅ DNS record events
    ├── file_event.py                  # ✅ Hosts file events
    ├── node_event.py                  # ✅ SWIM cluster events
    ├── system_event.py                # ✅ System lifecycle events
    ├── error_event.py                 # ✅ Error condition events
    └── health_event.py                # ✅ Health status events
```

**Implementation Status:**
- ✅ **Step 1.1.1**: Event system core COMPLETED
- ✅ **Step 1.1.2**: Event types COMPLETED  
- ✅ **Step 1.1.3**: Event registry COMPLETED
- ✅ **Step 1.1.4**: Event bus COMPLETED
- ✅ **Step 1.1.5**: Integration testing COMPLETED

**🚨 CRITICAL UPDATES NEEDED:**
- **Pydantic Integration**: Event data should use Pydantic models for validation
- **Type Hints**: Ensure all methods have proper type annotations
- **Documentation**: Add comprehensive docstrings following PEP 257
- **Test Activation**: Move tests from `tests/disabled/` to active test suite

#### 1.2 Dependency Injection System
**File Structure:**
```
app/joyride/injection/                 # ✅ IMPLEMENTED
├── __init__.py                        # ✅ DI system exports
├── config.py                          # ✅ Hierarchical configuration
├── providers/                         # ✅ Provider pattern implementation
│   ├── __init__.py
│   ├── provider_base.py               # ✅ Base provider types
│   ├── provider_registry.py          # ✅ Main DI registry
│   ├── singleton_provider.py         # ✅ Singleton lifecycle
│   ├── factory_provider.py           # ✅ Factory lifecycle
│   ├── prototype_provider.py         # ✅ Prototype lifecycle
│   └── class_provider.py             # ✅ Class-based provider
└── lifecycle/                         # ✅ Component lifecycle management
    ├── __init__.py
    ├── component.py                   # ✅ Component base classes
    ├── registry.py                    # ✅ Component registry
    ├── orchestrator.py               # ✅ Startup/shutdown coordination
    ├── health.py                     # ✅ Health monitoring
    ├── interfaces.py                 # ✅ Protocol definitions
    ├── types.py                      # ✅ Type definitions
    └── provider_adapter.py           # ✅ Provider-lifecycle integration
```

**Implementation Status:**
- ✅ **Step 1.2.1**: Configuration management COMPLETED
- ✅ **Step 1.2.2**: Provider pattern COMPLETED  
- ✅ **Step 1.2.3**: Lifecycle management COMPLETED
- ✅ **Step 1.2.4**: DI registry COMPLETED
- ✅ **Step 1.2.5**: Integration testing COMPLETED

**🚨 COMPLIANCE UPDATES NEEDED:**
- **Pydantic Configuration**: Replace Dict-based config with Pydantic models
- **Type Safety**: Ensure all provider methods have complete type annotations
- **Documentation**: Add comprehensive docstrings for all public methods
- **Error Handling**: Implement specific exception types with meaningful messages

### Phase 2: Code Quality and Composition Refactoring

#### 2.1 Python Coding Standards Compliance

**Implementation Steps:**
- [x] **Step 2.1.1**: Apply comprehensive code formatting and style
  - [x] Run Black formatter on all Python files: `uv run black app/ tests/`
  - [x] Run isort for consistent import ordering: `uv run isort app/ tests/`
  - [x] Apply consistent code style across entire codebase
  - [x] Update pyproject.toml with Black and isort configuration
  - [x] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [x] Mark this section's steps complete once all tests are passing

- [ ] **Step 2.1.2**: Comprehensive linting and static analysis
  - [ ] Run flake8 linter and fix all issues: `uv run flake8 app/ tests/`
  - [ ] Apply mypy for type checking and fix type issues
  - [ ] Run bandit for security scanning
  - [ ] Address all linting warnings and errors - **ZERO TOLERANCE FOR WARNINGS**
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 2.1.3**: Pydantic integration for data validation
  - [ ] Convert event data dictionaries to Pydantic models
  - [ ] Add validation for DNS record data (hostnames, IP addresses)
  - [ ] Implement configuration validation with Pydantic schemas
  - [ ] Replace plain Dict usage with typed Pydantic models
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 2.1.4**: Documentation and type safety
  - [ ] Ensure all functions and classes have proper docstrings following PEP 257
  - [ ] Add comprehensive type hints for all parameters and return values
  - [ ] Update inline comments to explain "WHY" not "WHAT"
  - [ ] Generate and review API documentation
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 2.1.5**: Test suite activation and cleanup
  - [ ] Evaluate the test in `tests/disabled/` and determine if they are still needed, if not remove them and skip the remaining steps in this section
  - [ ] Move tests from `tests/disabled/` to active test suite
  - [ ] Fix any failing tests and ensure 100% pass rate
  - [ ] Ensure test coverage meets >90% requirement
  - [ ] Update test naming to avoid "Test" prefix conflicts
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 2.2 Code Quality and Composition Refactoring
**Implementation Steps:**
- [ ] **Step 2.2.1**: Apply comprehensive code formatting
  - [ ] Run Black formatter on all Python files
  - [ ] Run isort for consistent import ordering
  - [ ] Apply consistent code style across entire codebase
  - [ ] Update pyproject.toml with Black and isort configuration
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 2.2.2**: Comprehensive linting and static analysis
  - [ ] Run flake8 linter and fix all issues
  - [ ] Apply mypy for type checking and fix type issues
  - [ ] Run bandit for security scanning
  - [ ] Address all linting warnings and errors
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 2.2.3**: Documentation cleanup
  - [ ] Ensure all functions and classes have proper docstrings
  - [ ] Update type hints for consistency
  - [ ] Review and update inline comments
  - [ ] Generate and review API documentation
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 2.3 Composition Over Inheritance Refactoring
**Objective**: Reduce code duplication and improve maintainability using composition patterns

**Implementation Steps:**
- [ ] **Step 2.3.1**: Create field descriptor system
  - [ ] Implement `EventField` descriptors for property access
  - [ ] Replace repetitive `@property` methods with declarative fields
  - [ ] Add type validation and default value support
  - [ ] **Test**: Create `tests/test_field_descriptors.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 2.3.2**: Implement validation mixins
  - [ ] Create `StringValidator`, `NumericValidator`, `ChoiceValidator` classes
  - [ ] Extract common validation patterns into reusable components
  - [ ] Replace repetitive validation code with mixin calls
  - [ ] **Test**: Create `tests/test_validation_mixins.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 2.3.3**: Event schema composition
  - [ ] Create `EventSchema` class for declarative event definitions
  - [ ] Define schemas for each event type using field descriptors
  - [ ] Implement schema-based validation and data handling
  - [ ] **Test**: Create `tests/test_event_schemas.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 2.3.4**: Event factory pattern
  - [ ] Implement `EventFactory` for consistent event creation
  - [ ] Simplify event `__init__` methods using factory pattern
  - [ ] Add factory-based event creation methods
  - [ ] **Test**: Create `tests/test_event_factory.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

**Benefits Expected:**
- **DRY Principle**: Eliminate ~200+ lines of repetitive property/validation code
- **Consistency**: All events follow identical patterns automatically
- **Maintainability**: Changes to validation logic propagate automatically
- **Extensibility**: Easy to add new field types and validation rules

### Phase 3: Event Producers (Sources) - 🚧 NEEDS IMPLEMENTATION

**UPDATED REQUIREMENTS:**
- Must follow Python coding standards with Pydantic models
- Use ENUMs for lifecycle events as specified
- Implement proper type hints and comprehensive docstrings
- Apply Black formatting and consistent code style

#### 3.1 Docker Event Producer
**File Structure:**
```
app/producers/
├── __init__.py
├── base.py          # Base producer class
├── docker.py        # Docker event producer
└── docker_events.py # Docker-specific event types
```

**Implementation Steps:**
- [ ] **Step 3.1.1**: Create `app/producers/base.py`
  - [ ] Implement `BaseEventProducer` abstract class
  - [ ] Add common producer functionality (event bus integration, lifecycle)
  - [ ] Include error handling and retry logic
  - [ ] **Test**: Create `tests/test_producers_base.py` with mock producer tests
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 3.1.2**: Create `app/producers/docker_events.py`
  - [ ] Define Docker-specific event ENUMs and classes with **Pydantic models**:
    - [ ] `DockerEventType` ENUM: `STARTED`, `STOPPED`, `DISCOVERED`
    - [ ] `DockerContainerEvent` class using the ENUM for event_type
    - [ ] **Pydantic models** for container metadata validation
    - [ ] **Strong type hints** for all parameters and return values
  - [ ] Include container metadata (name, labels, network info)
  - [ ] **Test**: Create `tests/test_docker_events.py` with event creation tests
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 3.1.3**: Create `app/producers/docker.py`
  - [ ] Implement `DockerEventProducer` class
  - [ ] Docker socket connection and event streaming
  - [ ] Container filtering based on labels/configuration
  - [ ] Support deferred container processing
  - [ ] **Test**: Create `tests/test_docker_producer.py` with Docker API mocking
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 3.1.4**: Docker producer integration testing
  - [ ] **Test**: Create `tests/test_docker_integration.py`
  - [ ] Test with real Docker containers (using test containers)
  - [ ] Test reconnection and error recovery
  - [ ] Performance tests with many containers
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 3.2 SWIM Event Producer  
**File Structure:**
```
app/producers/
├── swim.py          # SWIM event producer
└── swim_events.py   # SWIM-specific event types
```

**Implementation Steps:**
- [ ] **Step 3.2.1**: Create `app/producers/swim_events.py`
  - [ ] Define SWIM-specific event ENUMs and classes with **Pydantic models**:
    - [ ] `SwimEventType` ENUM: `NODE_DISCOVERED`, `NODE_JOINED`, `NODE_LEFT`, `NODE_FAILED`, `NODE_SUSPECTED`, `DNS_RECORD_SYNCED`, `SYNC_FORCED`, `CLUSTER_STATE_CHANGED`
    - [ ] `SwimNodeEvent` class using the ENUM for event_type
    - [ ] `SwimSyncEvent` class for DNS synchronization events
    - [ ] **Pydantic models** for node metadata and cluster state validation
  - [ ] Include node metadata and cluster state
  - [ ] **Test**: Create `tests/test_swim_events.py` with event validation tests
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 3.2.2**: Create `app/producers/swim.py`
  - [ ] Implement `SwimEventProducer` class
  - [ ] Integration with existing swimmies library
  - [ ] Configure SWIM settings from DI container
  - [ ] Handle SWIM protocol state changes
  - [ ] **Test**: Create `tests/test_swim_producer.py` with swimmies library mocking
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 3.2.3**: SWIM producer integration testing
  - [ ] **Test**: Create `tests/test_swim_integration.py`
  - [ ] Test with multiple SWIM nodes
  - [ ] Test network partitions and recovery
  - [ ] Test DNS record synchronization events
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 3.3 Hosts File Event Producer
**File Structure:**
```
app/producers/
├── hosts.py         # Hosts file event producer
└── hosts_events.py  # Hosts file-specific event types
```

**Implementation Steps:**
- [ ] **Step 3.3.1**: Create `app/producers/hosts_events.py`
  - [ ] Define file-specific event ENUMs and classes with **Pydantic models**:
    - [ ] `HostsEventType` ENUM: `FILE_CHANGED`, `RECORD_ADDED`, `RECORD_UPDATED`, `RECORD_REMOVED`, `FILE_CREATED`, `FILE_DELETED`, `DIRECTORY_SCANNED`
    - [ ] `HostsFileEvent` class using the ENUM for event_type
    - [ ] `HostsRecordEvent` class for DNS record changes
    - [ ] **Pydantic models** for file paths, timestamps, and record details validation
  - [ ] Include file paths, timestamps, and record details
  - [ ] **Test**: Create `tests/test_hosts_events.py` with event data validation
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 3.3.2**: Create `app/producers/hosts.py`
  - [ ] Implement `HostsFileEventProducer` class
  - [ ] File watching with configurable polling intervals
  - [ ] Support multiple hosts directories
  - [ ] File parsing and change detection logic
  - [ ] **Test**: Create `tests/test_hosts_producer.py` with filesystem mocking
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 3.3.3**: Hosts producer integration testing
  - [ ] **Test**: Create `tests/test_hosts_integration.py`
  - [ ] Test with real file system changes
  - [ ] Test with large hosts files and many directories
  - [ ] Test file permission and access error handling
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 3.4 System Event Producer
**File Structure:**
```
app/producers/
├── system.py        # System event producer
└── system_events.py # System-specific event types
```

**Implementation Steps:**
- [ ] **Step 3.4.1**: Create `app/producers/system_events.py`
  - [ ] Define system lifecycle event ENUMs and classes with **Pydantic models**:
    - [ ] `SystemEventType` ENUM: `SERVICE_STARTING`, `SERVICE_STARTED`, `SERVICE_STOPPING`, `SERVICE_STOPPED`, `SERVICE_FAILED`, `CONFIGURATION_CHANGED`, `HEALTH_CHECK_FAILED`, `HEALTH_CHECK_RECOVERED`
    - [ ] `ServiceLifecycleEvent` class using the ENUM for event_type
    - [ ] `ConfigurationEvent` class for config changes
    - [ ] `HealthCheckEvent` class for health status changes
    - [ ] **Pydantic models** for service names, error details, configuration changes validation
  - [ ] Include service names, error details, configuration changes
  - [ ] **Test**: Create `tests/test_system_events.py` with event creation tests
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 3.4.2**: Create `app/producers/system.py`
  - [ ] Implement `SystemEventProducer` class
  - [ ] Integration with DI injection system lifecycle
  - [ ] Health check monitoring and reporting
  - [ ] Configuration change detection
  - [ ] **Test**: Create `tests/test_system_producer.py` with lifecycle simulation
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 3.4.3**: System producer integration testing
  - [ ] **Test**: Create `tests/test_system_integration.py`
  - [ ] Test real component lifecycle events
  - [ ] Test configuration reload scenarios
  - [ ] Test health check failure and recovery
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

### Phase 4: Event Handlers (Consumers)

#### 4.1 DNS Record Handler
**File Structure:**
```
app/handlers/
├── __init__.py
├── base.py          # Base handler class
├── dns_record.py    # DNS record management handler
└── dns_backends/    # DNS server backend implementations
    ├── __init__.py
    ├── memory.py    # In-memory DNS backend
    └── dnslib.py    # dnslib-based backend
```

**Implementation Steps:**
- [ ] **Step 4.1.1**: Create `app/handlers/base.py`
  - [ ] Implement `BaseEventHandler` abstract class
  - [ ] Add common handler functionality (event filtering, error handling)
  - [ ] Include metrics collection and logging
  - [ ] **Test**: Create `tests/test_handlers_base.py` with mock handler tests
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.1.2**: Create `app/handlers/dns_backends/memory.py`
  - [ ] Implement in-memory DNS record storage
  - [ ] Support A, AAAA, CNAME record types
  - [ ] Include TTL and metadata management
  - [ ] Thread-safe operations
  - [ ] **Test**: Create `tests/test_dns_memory_backend.py` with record operations
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.1.3**: Create `app/handlers/dns_backends/dnslib.py`
  - [ ] Implement dnslib-based DNS backend
  - [ ] Integration with existing DNS server
  - [ ] Support existing DNS record format
  - [ ] **Test**: Create `tests/test_dns_dnslib_backend.py` with dnslib integration
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.1.4**: Create `app/handlers/dns_record.py`
  - [ ] Implement `DNSRecordHandler` class
  - [ ] Subscribe to Container, Node, and File events
  - [ ] DNS record addition/removal logic
  - [ ] Duplicate record prevention
  - [ ] **Test**: Create `tests/test_dns_record_handler.py` with event handling tests
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.1.5**: DNS handler integration testing
  - [ ] **Test**: Create `tests/test_dns_handler_integration.py`
  - [ ] Test complete event-to-DNS-record flow
  - [ ] Test with multiple backends
  - [ ] Performance tests with many records
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 4.2 Sync Handler
**File Structure:**
```
app/handlers/
├── sync.py          # DNS synchronization handler
└── sync_strategies/ # Conflict resolution strategies
    ├── __init__.py
    ├── timestamp.py # Timestamp-based resolution
    └── priority.py  # Priority-based resolution
```

**Implementation Steps:**
- [ ] **Step 4.2.1**: Create `app/handlers/sync_strategies/timestamp.py`
  - [ ] Implement timestamp-based conflict resolution
  - [ ] Handle clock skew and network delays
  - [ ] **Test**: Create `tests/test_sync_timestamp.py` with conflict scenarios
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.2.2**: Create `app/handlers/sync_strategies/priority.py`
  - [ ] Implement priority-based conflict resolution
  - [ ] Support node priorities and record sources
  - [ ] **Test**: Create `tests/test_sync_priority.py` with priority conflicts
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.2.3**: Create `app/handlers/sync.py`
  - [ ] Implement `SyncHandler` class
  - [ ] Handle Node and DNSRecordSynced events
  - [ ] Prevent circular sync calls with local_only pattern
  - [ ] Support configurable sync policies
  - [ ] **Test**: Create `tests/test_sync_handler.py` with sync logic tests
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.2.4**: Sync handler integration testing
  - [ ] **Test**: Create `tests/test_sync_integration.py`
  - [ ] Test distributed sync scenarios
  - [ ] Test conflict resolution strategies
  - [ ] Test circular dependency prevention
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 4.3 Logging and Monitoring Handlers
**File Structure:**
```
app/handlers/
├── logging.py       # Structured logging handler
├── metrics.py       # Metrics collection handler
└── health.py        # Health check handler
```

**Implementation Steps:**
- [ ] **Step 4.3.1**: Create `app/handlers/logging.py`
  - [ ] Implement `LoggingHandler` class
  - [ ] Structured logging for all event types
  - [ ] Configurable log levels and outputs
  - [ ] Event correlation and tracing
  - [ ] **Test**: Create `tests/test_logging_handler.py` with log output validation
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.3.2**: Create `app/handlers/metrics.py`
  - [ ] Implement `MetricsHandler` class
  - [ ] Event counts, timing, and error metrics
  - [ ] Support Prometheus-style metrics
  - [ ] **Test**: Create `tests/test_metrics_handler.py` with metrics collection
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.3.3**: Create `app/handlers/health.py`
  - [ ] Implement `HealthHandler` class
  - [ ] Monitor component health events
  - [ ] Aggregate system health status
  - [ ] **Test**: Create `tests/test_health_handler.py` with health scenarios
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.3.4**: Monitoring handlers integration testing
  - [ ] **Test**: Create `tests/test_monitoring_integration.py`
  - [ ] Test with high event volume
  - [ ] Test metrics accuracy and performance
  - [ ] Test health status aggregation
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 4.4 Validation and Error Handlers
**File Structure:**
```
app/handlers/
├── validation.py    # Input validation handler
├── error.py         # Error management handler
└── audit.py         # Audit logging handler
```

**Implementation Steps:**
- [ ] **Step 4.4.1**: Create `app/handlers/validation.py`
  - [ ] Implement `ValidationHandler` class
  - [ ] DNS hostname and IP address validation
  - [ ] Configuration validation
  - [ ] Input sanitization
  - [ ] **Test**: Create `tests/test_validation_handler.py` with validation cases
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.4.2**: Create `app/handlers/error.py`
  - [ ] Implement `ErrorHandler` class
  - [ ] Centralized error management
  - [ ] Retry logic for transient failures
  - [ ] Circuit breaker patterns
  - [ ] **Test**: Create `tests/test_error_handler.py` with error scenarios
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.4.3**: Create `app/handlers/audit.py`
  - [ ] Implement `AuditHandler` class
  - [ ] Event audit logging
  - [ ] Security event tracking
  - [ ] Configuration change auditing
  - [ ] **Test**: Create `tests/test_audit_handler.py` with audit trail validation
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 4.4.4**: Validation/Error handlers integration testing
  - [ ] **Test**: Create `tests/test_validation_error_integration.py`
  - [ ] Test error handling pipeline
  - [ ] Test validation with real data
  - [ ] Test audit trail completeness
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

### Phase 5: Configuration and Initialization

#### 5.1 Configuration System
**File Structure:**
```
app/config/
├── __init__.py
├── schema.py        # Configuration schema definitions
├── loader.py        # Configuration loading logic
├── validator.py     # Configuration validation
└── watcher.py       # Dynamic configuration updates
```

**Implementation Steps:**
- [ ] **Step 5.1.1**: Create `app/config/schema.py`
  - [ ] Define configuration schema using Pydantic or similar
  - [ ] Schema for each component (Docker, SWIM, DNS, etc.)
  - [ ] Environment variable mapping
  - [ ] Default values and validation rules
  - [ ] **Test**: Create `tests/test_config_schema.py` with schema validation
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 5.1.2**: Create `app/config/loader.py`
  - [ ] Implement hierarchical configuration loading
  - [ ] Support YAML, JSON, environment variables
  - [ ] Configuration merging and precedence rules
  - [ ] **Test**: Create `tests/test_config_loader.py` with various sources
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 5.1.3**: Create `app/config/validator.py`
  - [ ] Configuration validation against schema
  - [ ] Cross-component validation rules
  - [ ] Runtime configuration checks
  - [ ] **Test**: Create `tests/test_config_validator.py` with validation cases
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 5.1.4**: Create `app/config/watcher.py`
  - [ ] Dynamic configuration update detection
  - [ ] Configuration reload triggers
  - [ ] Component notification system
  - [ ] **Test**: Create `tests/test_config_watcher.py` with file watching
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 5.1.5**: Configuration system integration testing
  - [ ] **Test**: Create `tests/test_config_integration.py`
  - [ ] Test complete configuration lifecycle
  - [ ] Test dynamic updates and component reloading
  - [ ] Test configuration error handling
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 5.2 Application Bootstrapping
**File Structure:**
```
app/bootstrap/
├── __init__.py
├── application.py   # Main application class
├── factory.py       # Component factory
└── runner.py        # Application runner/entry point
```

**Implementation Steps:**
- [ ] **Step 5.2.1**: Create `app/bootstrap/factory.py`
  - [ ] Component factory using DI injection system
  - [ ] Configuration-driven component creation
  - [ ] Dependency graph resolution
  - [ ] **Test**: Create `tests/test_bootstrap_factory.py` with component creation
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 5.2.2**: Create `app/bootstrap/application.py`
  - [ ] Main application class coordinating all components
  - [ ] Graceful startup and shutdown handling
  - [ ] Component lifecycle management
  - [ ] Error handling and recovery
  - [ ] **Test**: Create `tests/test_bootstrap_application.py` with lifecycle tests
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 5.2.3**: Create `app/bootstrap/runner.py`
  - [ ] Application entry point
  - [ ] Command-line argument parsing
  - [ ] Different deployment modes (development, production)
  - [ ] Signal handling and graceful shutdown
  - [ ] **Test**: Create `tests/test_bootstrap_runner.py` with execution scenarios
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 5.2.4**: Bootstrap integration testing
  - [ ] **Test**: Create `tests/test_bootstrap_integration.py`
  - [ ] Test complete application startup
  - [ ] Test graceful shutdown scenarios
  - [ ] Test error recovery and restart
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

### Phase 6: Testing and Validation

#### 6.1 Unit Testing
**Testing Strategy:**
- **Isolation**: Each module tested independently with mocks
- **Coverage**: Minimum 90% code coverage for all modules
- **Documentation**: Test cases serve as component documentation
- **Automation**: All tests run in CI/CD pipeline

**Implementation Steps:**
- [ ] **Step 6.1.1**: Complete unit test coverage
  - [ ] Verify all components have comprehensive unit tests
  - [ ] Add missing test cases for edge conditions
  - [ ] Mock all external dependencies (Docker API, file system, network)
  - [ ] **Test**: Run `uv run pytest tests/unit/ --cov=app --cov-report=html`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 6.1.2**: Test data and fixtures
  - [ ] Create reusable test fixtures for common scenarios
  - [ ] Mock Docker containers with various configurations
  - [ ] Sample configuration files for different environments
  - [ ] **Test**: Create `tests/fixtures/` with reusable test data
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 6.1.3**: Performance unit tests
  - [ ] Test component performance under load
  - [ ] Memory usage validation
  - [ ] Event processing latency tests
  - [ ] **Test**: Create `tests/performance/` with benchmark tests
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 6.2 Integration Testing
**Testing Strategy:**
- **Component Integration**: Test component interactions
- **End-to-End Flows**: Test complete event workflows
- **External Systems**: Test with real Docker, file systems
- **Distributed Scenarios**: Test SWIM cluster behaviors

**Implementation Steps:**
- [ ] **Step 6.2.1**: Component integration tests
  - [ ] **Test**: Event flow from producers through bus to handlers
  - [ ] **Test**: DI injection system with real component dependencies
  - [ ] **Test**: Configuration system with dynamic updates
  - [ ] Create `tests/integration/test_component_integration.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 6.2.2**: End-to-end integration tests
  - [ ] **Test**: Complete Docker container → DNS record flow
  - [ ] **Test**: Hosts file changes → DNS record updates
  - [ ] **Test**: SWIM cluster events → DNS synchronization
  - [ ] Create `tests/integration/test_end_to_end.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 6.2.3**: External system integration tests
  - [ ] **Test**: Real Docker API integration using testcontainers
  - [ ] **Test**: File system monitoring with real files
  - [ ] **Test**: Network operations and error handling
  - [ ] Create `tests/integration/test_external_systems.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 6.2.4**: Distributed system integration tests
  - [ ] **Test**: Multi-node SWIM cluster synchronization
  - [ ] **Test**: Network partitions and recovery
  - [ ] **Test**: Conflict resolution in distributed scenarios
  - [ ] Create `tests/integration/test_distributed.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 6.2.5**: Failure and recovery testing
  - [ ] **Test**: Component failure scenarios
  - [ ] **Test**: Network failures and reconnection
  - [ ] **Test**: Configuration errors and recovery
  - [ ] **Test**: Resource exhaustion handling
  - [ ] Create `tests/integration/test_failure_recovery.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 6.3 Migration and Compatibility Testing
**Testing Strategy:**
- **Backwards Compatibility**: Ensure existing functionality works
- **Feature Parity**: Validate all existing features preserved
- **Performance**: No regression in performance metrics
- **Migration**: Test gradual migration scenarios

**Implementation Steps:**
- [ ] **Step 6.3.1**: Feature parity validation
  - [ ] **Test**: All existing DNS operations work identically
  - [ ] **Test**: Docker container discovery and monitoring
  - [ ] **Test**: Hosts file parsing and updates
  - [ ] **Test**: SWIM cluster functionality
  - [ ] Create `tests/migration/test_feature_parity.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 6.3.2**: Performance regression testing
  - [ ] **Test**: DNS query response times
  - [ ] **Test**: Event processing latency
  - [ ] **Test**: Memory usage under load
  - [ ] **Test**: Startup and shutdown times
  - [ ] Create `tests/migration/test_performance_regression.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 6.3.3**: Migration scenario testing
  - [ ] **Test**: Gradual component migration
  - [ ] **Test**: Feature flag controlled rollout
  - [ ] **Test**: Rollback to original system
  - [ ] Create `tests/migration/test_migration_scenarios.py`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

#### 6.4 Test Infrastructure and Automation
**Implementation Steps:**
- [ ] **Step 6.4.1**: Test environment setup
  - [ ] Docker Compose for test dependencies
  - [ ] Test database and file system setup
  - [ ] Mock external services configuration
  - [ ] Create `tests/docker-compose.test.yml`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 6.4.2**: Continuous Integration setup
  - [ ] GitHub Actions workflow for all test types
  - [ ] Test matrix for different Python versions
  - [ ] Code coverage reporting and enforcement
  - [ ] Update `.github/workflows/test.yml`
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

- [ ] **Step 6.4.3**: Test utilities and helpers
  - [ ] Common test utilities for component testing
  - [ ] Event assertion helpers
  - [ ] Mock factories for consistent test data
  - [ ] Create `tests/utils/` with helper modules
  - [ ] **Run Test**: `make test` should pass, fix any errors until all tests pass with no warnings
  - [ ] Mark this section's steps complete once all tests are passing

### Phase 7: Advanced Event Features (Future Enhancement)

#### 7.1 Event Bus Enhancements
- [ ] Add event filtering and routing capabilities
- [ ] Support event priority and ordering
- [ ] Implement event throttling and rate limiting
- [ ] Add event replay and persistence capabilities
- [ ] Support event transformation and enrichment

#### 7.2 Advanced Monitoring
- [ ] Event correlation and tracing across components
- [ ] Performance metrics and bottleneck detection
- [ ] Advanced alerting based on event patterns
- [ ] Event analytics and insights dashboard

#### 7.3 Plugin Architecture
- [ ] Dynamic event producer/handler loading
- [ ] Third-party plugin support
- [ ] Event middleware and interceptors
- [ ] Custom event type registration

## Implementation Strategy

### Incremental Development Approach
1. **Module-First Development**: Build and test each module independently
2. **Interface-Driven Design**: Define interfaces first, implement later
3. **Test-Driven Development**: Write tests before implementation
4. **Continuous Integration**: Each module fully tested before integration
5. **Feature Flags**: Use configuration to enable new vs old system
6. **Parallel Development**: Build new system alongside existing

### Module Development Workflow
Each module follows this development pattern:

#### Development Steps:
1. **Interface Definition**: Define abstract base classes and interfaces
2. **Test Creation**: Write comprehensive unit tests for the interface
3. **Implementation**: Implement concrete classes
4. **Unit Testing**: Achieve >90% test coverage
5. **Integration Testing**: Test module integration with dependencies
6. **Documentation**: Update code documentation and examples
7. **Performance Testing**: Validate performance requirements
8. **Code Review**: Peer review before merging

#### Module Dependencies:
```
Phase 1: Foundation (No dependencies)
├── events/ (base classes and interfaces)
└── injection/ (DI system)

Phase 2: Code Quality (Depends on Phase 1)
├── Python coding standards compliance
├── Pydantic integration
├── Documentation standards
└── Test suite activation

Phase 3: Producers (Depends on Phases 1-2)
├── producers/docker.py (depends on events/)
├── producers/swim.py (depends on events/, swimmies/)
├── producers/hosts.py (depends on events/)
└── producers/system.py (depends on events/, injection/)

Phase 4: Handlers (Depends on Phases 1-3)
├── handlers/dns_record.py (depends on events/, producers/)
├── handlers/sync.py (depends on events/, swimmies/)
├── handlers/logging.py (depends on events/)
├── handlers/metrics.py (depends on events/)
└── handlers/validation.py (depends on events/)

Phase 5: Configuration (Depends on Phases 1-4)
├── config/ (depends on injection/)
└── bootstrap/ (depends on all previous phases)

Phase 6: Testing (Tests all phases)
└── Complete test coverage and validation
```

### Testing Strategy

#### Test Types and Execution Order:
1. **Unit Tests**: Test individual classes and methods in isolation
2. **Component Tests**: Test module-level functionality
3. **Integration Tests**: Test component interactions
4. **End-to-End Tests**: Test complete workflows
5. **Performance Tests**: Validate performance requirements
6. **Migration Tests**: Test backwards compatibility

#### Test Commands:
```bash
# Run unit tests for specific module
uv run pytest tests/unit/test_events/ -v

# Run component integration tests
uv run pytest tests/component/test_docker_producer/ -v

# Run all tests with coverage
uv run pytest tests/ --cov=app --cov-report=html

# Run performance tests
uv run pytest tests/performance/ -v

# Run migration compatibility tests
uv run pytest tests/migration/ -v
```

### Development Environment Setup

#### Required Tools:
- **UV Package Manager**: For dependency management
- **pytest**: For testing framework
- **pytest-cov**: For coverage reporting
- **pytest-mock**: For mocking external dependencies
- **pytest-asyncio**: For async testing
- **testcontainers**: For integration testing with Docker

#### Development Dependencies:
```bash
# Add to pyproject.toml [project.optional-dependencies.dev]
uv add --group dev pytest pytest-cov pytest-mock pytest-asyncio
uv add --group dev testcontainers[docker] docker
uv add --group dev black isort flake8 mypy
```

### Migration and Rollback Strategy

#### Migration Phases:
1. **Preparation**: Build new system alongside existing
2. **Feature Flags**: Add configuration to switch between systems
3. **Component Migration**: Migrate one component at a time
4. **Validation**: Validate each component before proceeding
5. **Complete Migration**: Switch to new system entirely
6. **Cleanup**: Remove old system code

#### Rollback Plan:
- **Configuration Rollback**: Switch feature flags to use old system
- **Code Rollback**: Git branch rollback if needed
- **Data Preservation**: Ensure no data loss during migration
- **Performance Monitoring**: Monitor for regressions

#### Migration Feature Flags:
```yaml
# Configuration example
migration:
  use_new_event_system: true
  use_new_docker_producer: false  # Gradual rollout
  use_new_dns_handler: false
  fallback_to_legacy: true        # Automatic fallback on errors
```

### Risk Mitigation
- **Rollback Plan**: Ability to revert to original system
- **Feature Parity**: Ensure new system matches all existing functionality
- **Performance Monitoring**: Validate no performance regression
- **Documentation**: Update all documentation for new architecture

## Benefits Expected

### Development Benefits
- **Modularity**: Independent component development and testing
- **Extensibility**: Easy addition of new event sources and handlers
- **Testability**: Isolated unit testing with clear interfaces
- **Maintainability**: Clear separation of concerns and dependencies

### Operational Benefits
- **Reliability**: Better error isolation and recovery
- **Observability**: Enhanced logging and monitoring capabilities
- **Scalability**: Easier horizontal scaling of components
- **Configuration**: Dynamic configuration without code changes

### Future Benefits
- **Plugin Architecture**: Third-party event sources/handlers
- **Multiple DNS Backends**: Support different DNS server implementations
- **Advanced Sync**: Sophisticated conflict resolution and sync strategies
- **Cloud Integration**: Easy integration with cloud services and APIs

## Success Criteria

- [ ] All existing functionality preserved
- [ ] No performance degradation
- [ ] Improved test coverage (>90%)
- [ ] Reduced cyclomatic complexity
- [ ] Enhanced error handling and recovery
- [ ] Complete documentation coverage
- [ ] Zero-downtime deployment capability

## Timeline Estimate

**UPDATED TIMELINE WITH COMPLIANCE REQUIREMENTS:**

- **Phase 2 (Code Quality)**: 1-2 weeks **MUST BE COMPLETED FIRST**
- **Phase 1**: ✅ COMPLETED (Event System & DI)
- **Phase 3**: 2-3 weeks (Event Producers with Pydantic & ENUMs) 
- **Phase 4**: 2-3 weeks (Event Handlers with proper validation)
- **Phase 5**: 1-2 weeks (Configuration with Pydantic schemas)
- **Phase 6**: 2-3 weeks (Testing/Validation with activated test suite)

**Core Refactor Total**: 8-13 weeks

- **Phase 7**: 2-4 weeks (Advanced Features - Optional)

**Complete System Total**: 10-17 weeks

## Critical Actions Required

**IMMEDIATE PRIORITIES:**
1. **Fix code quality violations** (Phase 2.1) - CRITICAL for maintainability
2. **Activate disabled tests** - Essential for development confidence
3. **Apply Pydantic models** throughout event system
4. **Ensure zero linting warnings** - As per project standards

**BEFORE CONTINUING WITH PHASE 2:**
- All existing code must pass linting without warnings
- Disabled tests must be activated and passing
- Pydantic models must be implemented for existing event types
- Comprehensive type hints must be added throughout

This ensures Phase 2 implementation follows established coding standards from the beginning.

## Next Steps

This refactor will proceed incrementally with user approval for each phase. The first step is to implement the foundational event system infrastructure while maintaining full backwards compatibility with the existing codebase.
</content>
</invoke>
