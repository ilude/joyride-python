"""
Tests for Joyride Provider Pattern Implementation

This module tests component factories, dependency resolution, and lifecycle management
for the Joyride DNS Service dependency injection container.
"""

import threading
import time
from typing import Optional
from unittest.mock import Mock, patch

import pytest

from app.container.providers import (
    JoyrideCircularDependencyError,
    JoyrideClassProvider,
    JoyrideDependency,
    JoyrideDependencyResolutionError,
    JoyrideFactoryProvider,
    JoyrideLifecycleType,
    JoyridePrototypeProvider,
    JoyrideProvider,
    JoyrideProviderInfo,
    JoyrideProviderRegistry,
    JoyrideSingletonProvider,
)


# Helper classes for dependency injection testing
class MockService:
    """Simple test service."""
    
    def __init__(self, name: str = "test"):
        self.name = name
        self.created_at = time.time()
    
    def get_name(self) -> str:
        return self.name


class MockDependentService:
    """Service with dependencies."""
    
    def __init__(self, service: MockService, config: Optional[str] = None):
        self.service = service
        self.config = config
    
    def get_service_name(self) -> str:
        return self.service.get_name()


class MockPrototypeService:
    """Service that supports copying."""
    
    def __init__(self, value: int = 0):
        self.value = value
        self.created_at = time.time()
    
    def copy(self):
        """Create a copy of this service."""
        return MockPrototypeService(self.value)


class MockComplexService:
    """Service with multiple dependencies."""
    
    def __init__(self, service1: MockService, service2: MockDependentService, optional_param: str = "default"):
        self.service1 = service1
        self.service2 = service2
        self.optional_param = optional_param


class TestJoyrideDependency:
    """Test dependency specification."""
    
    def test_dependency_creation(self):
        """Test creating a dependency."""
        dep = JoyrideDependency(
            name="test_service",
            type_hint=MockService,
            required=True
        )
        
        assert dep.name == "test_service"
        assert dep.type_hint == MockService
        assert dep.required == True
        assert dep.default_value is None
    
    def test_dependency_with_default(self):
        """Test dependency with default value."""
        dep = JoyrideDependency(
            name="config",
            type_hint=str,
            required=False,
            default_value="default_config"
        )
        
        assert dep.name == "config"
        assert dep.type_hint == str
        assert dep.required == False
        assert dep.default_value == "default_config"
    
    def test_dependency_validation(self):
        """Test dependency validation."""
        # Invalid name
        with pytest.raises(ValueError, match="Dependency name must be a non-empty string"):
            JoyrideDependency("", MockService)
        
        # Invalid type hint
        with pytest.raises(ValueError, match="Type hint must be a type"):
            JoyrideDependency("test", "not a type")


class TestJoyrideProviderInfo:
    """Test provider information."""
    
    def test_provider_info_creation(self):
        """Test creating provider info."""
        provider = Mock(spec=JoyrideProvider)
        provider.name = "test"
        
        info = JoyrideProviderInfo(
            name="test_provider",
            provider=provider,
            lifecycle=JoyrideLifecycleType.SINGLETON
        )
        
        assert info.name == "test_provider"
        assert info.provider == provider
        assert info.lifecycle == JoyrideLifecycleType.SINGLETON
        assert info.dependencies == []
        assert info.created_instances == []
        assert info.metadata == {}
    
    def test_provider_info_validation(self):
        """Test provider info validation."""
        provider = Mock(spec=JoyrideProvider)
        
        # Invalid name
        with pytest.raises(ValueError, match="Provider name must be a non-empty string"):
            JoyrideProviderInfo("", provider, JoyrideLifecycleType.SINGLETON)
        
        # Invalid provider
        with pytest.raises(ValueError, match="Provider must be a JoyrideProvider instance"):
            JoyrideProviderInfo("test", "not a provider", JoyrideLifecycleType.SINGLETON)
        
        # Invalid lifecycle
        with pytest.raises(ValueError, match="Lifecycle must be a JoyrideLifecycleType"):
            JoyrideProviderInfo("test", provider, "not a lifecycle")


class TestJoyrideSingletonProvider:
    """Test singleton provider."""
    
    def test_singleton_creation(self):
        """Test creating a singleton provider."""
        def factory():
            return MockService("singleton")
        
        provider = JoyrideSingletonProvider("test_singleton", factory)
        
        assert provider.name == "test_singleton"
        assert provider._factory == factory
        assert provider._dependencies == []
        assert provider._instance is None
        assert provider._created == False
    
    def test_singleton_with_dependencies(self):
        """Test singleton with dependencies."""
        deps = [JoyrideDependency("config", str, required=True)]
        
        def factory(config: str):
            return MockService(config)
        
        provider = JoyrideSingletonProvider("test_singleton", factory, deps)
        
        assert provider.get_dependencies() == deps
    
    def test_singleton_instance_creation(self):
        """Test singleton instance creation."""
        call_count = 0
        
        def factory():
            nonlocal call_count
            call_count += 1
            return MockService("singleton")
        
        provider = JoyrideSingletonProvider("test_singleton", factory)
        registry = Mock()
        
        # First call should create instance
        instance1 = provider.create(registry)
        assert call_count == 1
        assert isinstance(instance1, MockService)
        assert instance1.name == "singleton"
        
        # Second call should return same instance
        instance2 = provider.create(registry)
        assert call_count == 1  # Factory not called again
        assert instance1 is instance2
    
    def test_singleton_can_create(self):
        """Test singleton can_create method."""
        def factory():
            return MockService()
        
        provider = JoyrideSingletonProvider("test_singleton", factory)
        registry = Mock()
        registry.has_provider.return_value = True
        
        assert provider.can_create(registry) == True
    
    def test_singleton_with_missing_dependency(self):
        """Test singleton with missing dependency."""
        deps = [JoyrideDependency("missing_service", MockService, required=True)]
        
        def factory(missing_service: MockService):
            return MockDependentService(missing_service)
        
        provider = JoyrideSingletonProvider("test_singleton", factory, deps)
        registry = Mock()
        registry.has_provider.return_value = False
        
        assert provider.can_create(registry) == False
    
    def test_singleton_reset(self):
        """Test singleton reset functionality."""
        def factory():
            return MockService("singleton")
        
        provider = JoyrideSingletonProvider("test_singleton", factory)
        registry = Mock()
        
        # Create instance
        instance = provider.create(registry)
        assert provider._created == True
        assert provider._instance is not None
        
        # Reset
        provider.reset()
        assert provider._created == False
        assert provider._instance is None
    
    def test_singleton_validation(self):
        """Test singleton provider validation."""
        # Invalid factory
        with pytest.raises(ValueError, match="Factory must be callable"):
            JoyrideSingletonProvider("test", "not callable")


class TestJoyrideFactoryProvider:
    """Test factory provider."""
    
    def test_factory_creation(self):
        """Test creating a factory provider."""
        def factory():
            return MockService("factory")
        
        provider = JoyrideFactoryProvider("test_factory", factory)
        
        assert provider.name == "test_factory"
        assert provider._factory == factory
        assert provider._dependencies == []
    
    def test_factory_instance_creation(self):
        """Test factory instance creation."""
        call_count = 0
        
        def factory():
            nonlocal call_count
            call_count += 1
            return MockService(f"factory_{call_count}")
        
        provider = JoyrideFactoryProvider("test_factory", factory)
        registry = Mock()
        
        # Each call should create new instance
        instance1 = provider.create(registry)
        assert call_count == 1
        assert instance1.name == "factory_1"
        
        instance2 = provider.create(registry)
        assert call_count == 2
        assert instance2.name == "factory_2"
        
        # Instances should be different
        assert instance1 is not instance2
    
    def test_factory_with_dependencies(self):
        """Test factory with dependencies."""
        deps = [
            JoyrideDependency("service", MockService, required=True),
            JoyrideDependency("config", str, required=False, default_value="default")
        ]
        
        def factory(service: MockService, config: str = "default"):
            return MockDependentService(service, config)
        
        provider = JoyrideFactoryProvider("test_factory", factory, deps)
        registry = Mock()
        
        # Mock registry to return MockService for "service" and raise error for "config"
        def mock_get(name):
            if name == "service":
                return MockService(name)
            else:
                raise JoyrideDependencyResolutionError(f"Provider '{name}' not found")
        
        registry.get.side_effect = mock_get
        
        instance = provider.create(registry)
        assert isinstance(instance, MockDependentService)
        assert instance.config == "default"
    
    def test_factory_validation(self):
        """Test factory provider validation."""
        # Invalid factory
        with pytest.raises(ValueError, match="Factory must be callable"):
            JoyrideFactoryProvider("test", "not callable")


class TestJoyridePrototypeProvider:
    """Test prototype provider."""
    
    def test_prototype_creation(self):
        """Test creating a prototype provider."""
        prototype = MockPrototypeService(42)
        provider = JoyridePrototypeProvider("test_prototype", prototype)
        
        assert provider.name == "test_prototype"
        assert provider._prototype == prototype
        assert provider._clone_method == "copy"
    
    def test_prototype_instance_creation(self):
        """Test prototype instance creation."""
        prototype = MockPrototypeService(42)
        provider = JoyridePrototypeProvider("test_prototype", prototype)
        registry = Mock()
        
        # Each call should create new instance via cloning
        instance1 = provider.create(registry)
        instance2 = provider.create(registry)
        
        assert isinstance(instance1, MockPrototypeService)
        assert isinstance(instance2, MockPrototypeService)
        assert instance1.value == 42
        assert instance2.value == 42
        assert instance1 is not instance2
        assert instance1 is not prototype
    
    def test_prototype_custom_clone_method(self):
        """Test prototype with custom clone method."""
        class CustomPrototype:
            def __init__(self, value):
                self.value = value
            
            def clone(self):
                return CustomPrototype(self.value * 2)
        
        prototype = CustomPrototype(10)
        provider = JoyridePrototypeProvider("test_prototype", prototype, "clone")
        registry = Mock()
        
        instance = provider.create(registry)
        assert instance.value == 20  # Doubled by custom clone method
    
    def test_prototype_can_create(self):
        """Test prototype can_create method."""
        prototype = MockPrototypeService(42)
        provider = JoyridePrototypeProvider("test_prototype", prototype)
        registry = Mock()
        
        # Prototype can always create
        assert provider.can_create(registry) == True
    
    def test_prototype_no_dependencies(self):
        """Test prototype has no dependencies."""
        prototype = MockPrototypeService(42)
        provider = JoyridePrototypeProvider("test_prototype", prototype)
        
        assert provider.get_dependencies() == []
    
    def test_prototype_validation(self):
        """Test prototype provider validation."""
        class BadPrototype:
            pass
        
        # Missing clone method
        with pytest.raises(ValueError, match="Prototype does not have method 'copy'"):
            JoyridePrototypeProvider("test", BadPrototype(), "copy")


class TestJoyrideClassProvider:
    """Test class provider."""
    
    def test_class_provider_creation(self):
        """Test creating a class provider."""
        provider = JoyrideClassProvider("test_class", MockService)
        
        assert provider.name == "test_class"
        assert provider._cls == MockService
        assert provider._lifecycle == JoyrideLifecycleType.FACTORY
    
    def test_class_provider_dependency_analysis(self):
        """Test automatic dependency analysis."""
        provider = JoyrideClassProvider("test_class", MockDependentService)
        dependencies = provider.get_dependencies()
        
        assert len(dependencies) == 2
        
        # Check service dependency
        service_dep = next(dep for dep in dependencies if dep.name == "service")
        assert service_dep.type_hint == MockService
        assert service_dep.required == True
        
        # Check config dependency
        config_dep = next(dep for dep in dependencies if dep.name == "config")
        assert config_dep.required == False
        assert config_dep.default_value is None
    
    def test_class_provider_instance_creation(self):
        """Test class provider instance creation."""
        provider = JoyrideClassProvider("test_class", MockService)
        registry = Mock()
        # Make registry.get raise exception to force using defaults
        registry.get.side_effect = lambda name: (_ for _ in ()).throw(
            JoyrideDependencyResolutionError(f"Provider '{name}' is not registered")
        )
        
        instance = provider.create(registry)
        assert isinstance(instance, MockService)
        assert instance.name == "test"  # Default value
    
    def test_class_provider_with_dependencies(self):
        """Test class provider with dependencies."""
        provider = JoyrideClassProvider("test_class", MockDependentService)
        registry = Mock()
        
        # Mock dependency resolution
        test_service = MockService("dependency")
        registry.get.return_value = test_service
        
        instance = provider.create(registry, config="injected_config")
        assert isinstance(instance, MockDependentService)
        assert instance.service == test_service
        assert instance.config == "injected_config"
    
    def test_class_provider_singleton_lifecycle(self):
        """Test class provider with singleton lifecycle."""
        provider = JoyrideClassProvider("test_class", MockService, JoyrideLifecycleType.SINGLETON)
        registry = Mock()
        
        # First call creates instance
        instance1 = provider.create(registry)
        assert isinstance(instance1, MockService)
        
        # Second call returns same instance
        instance2 = provider.create(registry)
        assert instance1 is instance2
    
    def test_class_provider_validation(self):
        """Test class provider validation."""
        # Invalid class
        with pytest.raises(ValueError, match="cls must be a class"):
            JoyrideClassProvider("test", "not a class")


class TestJoyrideProviderRegistry:
    """Test provider registry."""
    
    def test_registry_creation(self):
        """Test creating a provider registry."""
        registry = JoyrideProviderRegistry()
        
        assert registry._providers == {}
        assert registry._resolution_stack == []
    
    def test_register_provider(self):
        """Test registering a provider."""
        registry = JoyrideProviderRegistry()
        provider = JoyrideSingletonProvider("test", lambda: MockService())
        
        registry.register_provider(provider, JoyrideLifecycleType.SINGLETON)
        
        assert registry.has_provider("test")
        assert registry.get_provider_count() == 1
        assert "test" in registry.get_provider_names()
    
    def test_register_duplicate_provider(self):
        """Test registering duplicate provider."""
        registry = JoyrideProviderRegistry()
        provider = JoyrideSingletonProvider("test", lambda: MockService())
        
        registry.register_provider(provider, JoyrideLifecycleType.SINGLETON)
        
        # Try to register again
        with pytest.raises(ValueError, match="Provider 'test' is already registered"):
            registry.register_provider(provider, JoyrideLifecycleType.SINGLETON)
    
    def test_register_singleton_helper(self):
        """Test register_singleton helper method."""
        registry = JoyrideProviderRegistry()
        
        provider = registry.register_singleton("test", lambda: MockService())
        
        assert isinstance(provider, JoyrideSingletonProvider)
        assert registry.has_provider("test")
    
    def test_register_factory_helper(self):
        """Test register_factory helper method."""
        registry = JoyrideProviderRegistry()
        
        provider = registry.register_factory("test", lambda: MockService())
        
        assert isinstance(provider, JoyrideFactoryProvider)
        assert registry.has_provider("test")
    
    def test_register_prototype_helper(self):
        """Test register_prototype helper method."""
        registry = JoyrideProviderRegistry()
        prototype = MockPrototypeService(42)
        
        provider = registry.register_prototype("test", prototype)
        
        assert isinstance(provider, JoyridePrototypeProvider)
        assert registry.has_provider("test")
    
    def test_register_class_helper(self):
        """Test register_class helper method."""
        registry = JoyrideProviderRegistry()
        
        provider = registry.register_class("test", MockService)
        
        assert isinstance(provider, JoyrideClassProvider)
        assert registry.has_provider("test")
    
    def test_unregister_provider(self):
        """Test unregistering a provider."""
        registry = JoyrideProviderRegistry()
        registry.register_singleton("test", lambda: MockService())
        
        assert registry.has_provider("test")
        
        registry.unregister_provider("test")
        
        assert not registry.has_provider("test")
        assert registry.get_provider_count() == 0
    
    def test_unregister_nonexistent_provider(self):
        """Test unregistering non-existent provider."""
        registry = JoyrideProviderRegistry()
        
        with pytest.raises(ValueError, match="Provider 'nonexistent' is not registered"):
            registry.unregister_provider("nonexistent")
    
    def test_get_instance(self):
        """Test getting instances from registry."""
        registry = JoyrideProviderRegistry()
        registry.register_singleton("test", lambda: MockService("registry_test"))
        
        instance = registry.get("test")
        assert isinstance(instance, MockService)
        assert instance.name == "registry_test"
    
    def test_get_nonexistent_provider(self):
        """Test getting from non-existent provider."""
        registry = JoyrideProviderRegistry()
        
        with pytest.raises(JoyrideDependencyResolutionError, match="Provider 'nonexistent' is not registered"):
            registry.get("nonexistent")
    
    def test_dependency_resolution(self):
        """Test automatic dependency resolution."""
        registry = JoyrideProviderRegistry()
        
        # Register dependencies in reverse order
        registry.register_class("dependent", MockDependentService)
        registry.register_singleton("service", lambda: MockService("dependency"))
        
        # Get dependent service - should auto-resolve dependencies
        instance = registry.get("dependent")
        assert isinstance(instance, MockDependentService)
        assert instance.service.name == "dependency"
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        registry = JoyrideProviderRegistry()
        
        # Create circular dependency
        deps_a = [JoyrideDependency("service_b", str, required=True)]
        deps_b = [JoyrideDependency("service_a", str, required=True)]
        
        registry.register_factory("service_a", lambda service_b: f"A depends on {service_b}", deps_a)
        registry.register_factory("service_b", lambda service_a: f"B depends on {service_a}", deps_b)
        
        with pytest.raises(JoyrideCircularDependencyError) as exc_info:
            registry.get("service_a")
        
        assert "service_a" in str(exc_info.value)
        assert "service_b" in str(exc_info.value)
    
    def test_dependency_graph(self):
        """Test dependency graph generation."""
        registry = JoyrideProviderRegistry()
        
        # Register services with dependencies
        registry.register_class("complex", MockComplexService)
        registry.register_class("dependent", MockDependentService)
        registry.register_singleton("service", lambda: MockService())
        registry.register_singleton("service1", lambda: MockService("service1"))
        registry.register_singleton("service2", lambda: MockService("service2"))
        
        graph = registry.get_dependency_graph()
        
        assert "service" in graph
        assert "dependent" in graph
        assert "complex" in graph
        assert "service1" in graph
        assert "service2" in graph
        
        # Check dependencies
        assert "service" in graph["dependent"]
        assert "service1" in graph["complex"]
        assert "service2" in graph["complex"]
    
    def test_validate_dependencies(self):
        """Test dependency validation."""
        registry = JoyrideProviderRegistry()
        
        # Register service with missing dependency
        deps = [JoyrideDependency("missing_service", MockService, required=True)]
        registry.register_factory("broken", lambda missing_service: MockService(), deps)
        
        errors = registry.validate_dependencies()
        assert len(errors) > 0
        assert "missing required dependency 'missing_service'" in errors[0]
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = JoyrideProviderRegistry()
        
        registry.register_singleton("test1", lambda: MockService())
        registry.register_factory("test2", lambda: MockService())
        
        assert registry.get_provider_count() == 2
        
        registry.clear()
        
        assert registry.get_provider_count() == 0
        assert registry.get_provider_names() == []
    
    def test_thread_safety(self):
        """Test thread safety of provider registry."""
        registry = JoyrideProviderRegistry()
        registry.register_singleton("test", lambda: MockService("thread_test"))
        
        instances = []
        errors = []
        
        def worker():
            try:
                instance = registry.get("test")
                instances.append(instance)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0
        assert len(instances) == 10
        
        # All instances should be the same (singleton)
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance


class TestProviderIntegration:
    """Integration tests for provider system."""
    
    def test_complex_dependency_resolution(self):
        """Test complex dependency resolution scenario."""
        registry = JoyrideProviderRegistry()
        
        # Register services to match parameter names
        registry.register_class("complex", MockComplexService)
        registry.register_singleton("service1", lambda: MockService("service1"))
        registry.register_singleton("service", lambda: MockService("for_service2"))  # For MockDependentService
        registry.register_class("service2", MockDependentService)
        
        # Get complex service - should resolve all dependencies
        instance = registry.get("complex", optional_param="custom")
        
        assert isinstance(instance, MockComplexService)
        assert isinstance(instance.service1, MockService)
        assert isinstance(instance.service2, MockDependentService)
        assert instance.service1.name == "service1"
        assert instance.service2.service.name == "for_service2"
        assert instance.optional_param == "custom"
    
    def test_mixed_lifecycle_scenario(self):
        """Test scenario with mixed lifecycle types."""
        registry = JoyrideProviderRegistry()
        
        # Singleton base service
        registry.register_singleton("base", lambda: MockService("base"))
        
        # Register provider that matches parameter name 'service' for MockDependentService
        registry.register_singleton("service", lambda: MockService("shared"))
        
        # Factory service that depends on singleton
        registry.register_class("factory_service", MockDependentService)
        
        # Prototype service
        prototype = MockPrototypeService(100)
        registry.register_prototype("prototype", prototype)
        
        # Get multiple instances
        factory1 = registry.get("factory_service")
        factory2 = registry.get("factory_service")
        
        proto1 = registry.get("prototype")
        proto2 = registry.get("prototype")
        
        # Factory instances should be different
        assert factory1 is not factory2
        
        # But should share same singleton dependency
        assert factory1.service.name == "shared"
        assert factory2.service.name == "shared"
        # Since both use same singleton provider, they should be same instance
        assert factory1.service is factory2.service
        
        # Prototype instances should be different
        assert proto1 is not proto2
        assert proto1.value == proto2.value == 100
    
    def test_provider_replacement(self):
        """Test replacing a provider."""
        registry = JoyrideProviderRegistry()
        
        # Register initial provider
        registry.register_singleton("service", lambda: MockService("original"))
        
        original_instance = registry.get("service")
        assert original_instance.name == "original"
        
        # Replace provider
        registry.unregister_provider("service")
        registry.register_singleton("service", lambda: MockService("replacement"))
        
        new_instance = registry.get("service")
        assert new_instance.name == "replacement"
        assert new_instance is not original_instance
