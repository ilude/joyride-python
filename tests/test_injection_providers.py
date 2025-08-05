"""
Tests for Joyride Provider Pattern Implementation

This module tests component factories, dependency resolution, and lifecycle management
for the Joyride DNS Service dependency injection container.
"""

import sys
import threading
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add tests/support to path for imports
sys.path.append(str(Path(__file__).parent / "support"))

from injection_helpers import (  # noqa: E402
    ComplexService,
    DependentService,
    PrototypeService,
    SimpleService,
)

from app.joyride.injection.providers import (  # noqa: E402
    CircularDependencyError,
    ClassProvider,
    Dependency,
    DependencyResolutionError,
    FactoryProvider,
    LifecycleType,
    PrototypeProvider,
    Provider,
    ProviderInfo,
    ProviderRegistry,
    SingletonProvider,
)

# Aliases for backward compatibility with existing tests
TestService = SimpleService
TestDependentService = DependentService
TestComplexService = ComplexService
TestPrototypeService = PrototypeService

# Mock classes used in tests - aliases to imported services
MockService = SimpleService
MockDependentService = DependentService
MockComplexService = ComplexService
MockPrototypeService = PrototypeService


class TestDependency:
    """Test dependency specification."""

    def test_dependency_creation(self):
        """Test creating a dependency."""
        dep = Dependency(
            name="test_service", type_hint=TestService, required=True
        )

        assert dep.name == "test_service"
        assert dep.type_hint == TestService
        assert dep.required is True
        assert dep.default_value is None

    def test_dependency_with_default(self):
        """Test dependency with default value."""
        dep = Dependency(
            name="config", type_hint=str, required=False, default_value="default_config"
        )

        assert dep.name == "config"
        assert dep.type_hint == str
        assert dep.required is False
        assert dep.default_value == "default_config"

    def test_dependency_validation(self):
        """Test dependency validation."""
        # Invalid name
        with pytest.raises(
            ValueError, match="Dependency name must be a non-empty string"
        ):
            Dependency("", TestService)

        # Invalid type hint
        with pytest.raises(ValueError, match="Type hint must be a type"):
            Dependency("test", "not a type")


class TestProviderInfo:
    """Test provider information."""

    def test_provider_info_creation(self):
        """Test creating provider info."""
        provider = Mock(spec=Provider)
        provider.name = "test"

        info = ProviderInfo(
            name="test_provider",
            provider=provider,
            lifecycle=LifecycleType.SINGLETON,
        )

        assert info.name == "test_provider"
        assert info.provider == provider
        assert info.lifecycle == LifecycleType.SINGLETON
        assert info.dependencies == []
        assert info.created_instances == []
        assert info.metadata == {}

    def test_provider_info_validation(self):
        """Test provider info validation."""
        provider = Mock(spec=Provider)

        # Invalid name
        with pytest.raises(
            ValueError, match="Provider name must be a non-empty string"
        ):
            ProviderInfo("", provider, LifecycleType.SINGLETON)

        # Invalid provider
        with pytest.raises(
            ValueError, match="Provider must be a Provider instance"
        ):
            ProviderInfo(
                "test", "not a provider", LifecycleType.SINGLETON
            )

        # Invalid lifecycle
        with pytest.raises(
            ValueError, match="Lifecycle must be a LifecycleType"
        ):
            ProviderInfo("test", provider, "not a lifecycle")


class TestSingletonProvider:
    """Test singleton provider."""

    def test_singleton_creation(self):
        """Test creating a singleton provider."""

        def factory():
            return TestService("singleton")

        provider = SingletonProvider("test_singleton", factory)

        assert provider.name == "test_singleton"
        assert provider._factory == factory
        assert provider._dependencies == []
        assert provider._instance is None
        assert provider._created is False

    def test_singleton_with_dependencies(self):
        """Test singleton with dependencies."""
        deps = [Dependency("config", str, required=True)]

        def factory(config: str):
            return TestService(config)

        provider = SingletonProvider("test_singleton", factory, deps)

        assert provider.get_dependencies() == deps

    def test_singleton_instance_creation(self):
        """Test singleton instance creation."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return TestService("singleton")

        provider = SingletonProvider("test_singleton", factory)
        registry = Mock()

        # First call should create instance
        instance1 = provider.create(registry)
        assert call_count == 1
        assert isinstance(instance1, TestService)
        assert instance1.name == "singleton"

        # Second call should return same instance
        instance2 = provider.create(registry)
        assert call_count == 1  # Factory not called again
        assert instance1 is instance2

    def test_singleton_can_create(self):
        """Test singleton can_create method."""

        def factory():
            return TestService()

        provider = SingletonProvider("test_singleton", factory)
        registry = Mock()
        registry.has_provider.return_value = True

        assert provider.can_create(registry) is True

    def test_singleton_with_missing_dependency(self):
        """Test singleton with missing dependency."""
        deps = [Dependency("missing_service", TestService, required=True)]

        def factory(missing_service: TestService):
            return TestDependentService(missing_service)

        provider = SingletonProvider("test_singleton", factory, deps)
        registry = Mock()
        registry.has_provider.return_value = False

        assert provider.can_create(registry) is False

    def test_singleton_reset(self):
        """Test singleton reset functionality."""

        def factory():
            return TestService("singleton")

        provider = SingletonProvider("test_singleton", factory)
        registry = Mock()

        # Create instance
        instance = provider.create(registry)  # noqa: F841
        assert provider._created is True
        assert provider._instance is not None

        # Reset
        provider.reset()
        assert provider._created is False
        assert provider._instance is None

    def test_singleton_validation(self):
        """Test singleton provider validation."""
        # Invalid factory
        with pytest.raises(ValueError, match="Factory must be callable"):
            SingletonProvider("test", "not callable")


class TestFactoryProvider:
    """Test factory provider."""

    def test_factory_creation(self):
        """Test creating a factory provider."""

        def factory():
            return TestService("factory")

        provider = FactoryProvider("test_factory", factory)

        assert provider.name == "test_factory"
        assert provider._factory == factory
        assert provider._dependencies == []

    def test_factory_instance_creation(self):
        """Test factory instance creation."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return TestService(f"factory_{call_count}")

        provider = FactoryProvider("test_factory", factory)
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
            Dependency("service", TestService, required=True),
            Dependency("config", str, required=False, default_value="default"),
        ]

        def factory(service: TestService, config: str = "default"):
            return TestDependentService(service, config)

        provider = FactoryProvider("test_factory", factory, deps)
        registry = Mock()

        # Mock registry to return TestService for "service" and raise error for "config"
        def mock_get(name):
            if name == "service":
                return TestService(name)
            else:
                raise DependencyResolutionError(f"Provider '{name}' not found")

        registry.get.side_effect = mock_get

        instance = provider.create(registry)
        assert isinstance(instance, TestDependentService)
        assert instance.config == "default"

    def test_factory_validation(self):
        """Test factory provider validation."""
        # Invalid factory
        with pytest.raises(ValueError, match="Factory must be callable"):
            FactoryProvider("test", "not callable")


class TestPrototypeProvider:
    """Test prototype provider."""

    def test_prototype_creation(self):
        """Test creating a prototype provider."""
        prototype = TestPrototypeService(42)
        provider = PrototypeProvider("test_prototype", prototype)

        assert provider.name == "test_prototype"
        assert provider._prototype == prototype
        assert provider._clone_method == "copy"

    def test_prototype_instance_creation(self):
        """Test prototype instance creation."""
        prototype = TestPrototypeService(42)
        provider = PrototypeProvider("test_prototype", prototype)
        registry = Mock()

        # Each call should create new instance via cloning
        instance1 = provider.create(registry)
        instance2 = provider.create(registry)

        assert isinstance(instance1, TestPrototypeService)
        assert isinstance(instance2, TestPrototypeService)
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
        provider = PrototypeProvider("test_prototype", prototype, "clone")
        registry = Mock()

        instance = provider.create(registry)
        assert instance.value == 20  # Doubled by custom clone method

    def test_prototype_can_create(self):
        """Test prototype can_create method."""
        prototype = TestPrototypeService(42)
        provider = PrototypeProvider("test_prototype", prototype)
        registry = Mock()

        # Prototype can always create
        assert provider.can_create(registry) is True

    def test_prototype_no_dependencies(self):
        """Test prototype has no dependencies."""
        prototype = TestPrototypeService(42)
        provider = PrototypeProvider("test_prototype", prototype)

        assert provider.get_dependencies() == []

    def test_prototype_validation(self):
        """Test prototype provider validation."""

        class BadPrototype:
            pass

        # Missing clone method
        with pytest.raises(ValueError, match="Prototype does not have method 'copy'"):
            PrototypeProvider("test", BadPrototype(), "copy")


class TestClassProvider:
    """Test class provider."""

    def test_class_provider_creation(self):
        """Test creating a class provider."""
        provider = ClassProvider("test_class", TestService)

        assert provider.name == "test_class"
        assert provider._cls == TestService
        assert provider._lifecycle == LifecycleType.FACTORY

    def test_class_provider_dependency_analysis(self):
        """Test automatic dependency analysis."""
        provider = ClassProvider("test_class", TestDependentService)
        dependencies = provider.get_dependencies()

        assert len(dependencies) == 2

        # Check service dependency
        service_dep = next(dep for dep in dependencies if dep.name == "service")
        assert service_dep.type_hint == TestService
        assert service_dep.required is True

        # Check config dependency
        config_dep = next(dep for dep in dependencies if dep.name == "config")
        assert config_dep.required is False
        assert config_dep.default_value is None

    def test_class_provider_instance_creation(self):
        """Test class provider instance creation."""
        provider = ClassProvider("test_class", TestService)
        registry = Mock()
        # Make registry.get raise exception to force using defaults
        registry.get.side_effect = lambda name: (_ for _ in ()).throw(
            DependencyResolutionError(f"Provider '{name}' is not registered")
        )

        instance = provider.create(registry)
        assert isinstance(instance, TestService)
        assert instance.name == "test"  # Default value

    def test_class_provider_with_dependencies(self):
        """Test class provider with dependencies."""
        provider = ClassProvider("test_class", TestDependentService)
        registry = Mock()

        # Mock dependency resolution
        test_service = TestService("dependency")
        registry.get.return_value = test_service

        instance = provider.create(registry, config="injected_config")
        assert isinstance(instance, TestDependentService)
        assert instance.service == test_service
        assert instance.config == "injected_config"

    def test_class_provider_singleton_lifecycle(self):
        """Test class provider with singleton lifecycle."""
        provider = ClassProvider(
            "test_class", TestService, LifecycleType.SINGLETON
        )
        registry = Mock()

        # First call creates instance
        instance1 = provider.create(registry)
        assert isinstance(instance1, TestService)

        # Second call returns same instance
        instance2 = provider.create(registry)
        assert instance1 is instance2

    def test_class_provider_validation(self):
        """Test class provider validation."""
        # Invalid class
        with pytest.raises(ValueError, match="cls must be a class"):
            ClassProvider("test", "not a class")


class TestProviderRegistry:
    """Test provider registry."""

    def test_registry_creation(self):
        """Test creating a provider registry."""
        registry = ProviderRegistry()

        assert registry._providers == {}
        assert registry._resolution_stack == []

    def test_register_provider(self):
        """Test registering a provider."""
        registry = ProviderRegistry()
        provider = SingletonProvider("test", lambda: TestService())

        registry.register_provider(provider, LifecycleType.SINGLETON)

        assert registry.has_provider("test")
        assert registry.get_provider_count() == 1
        assert "test" in registry.get_provider_names()

    def test_register_duplicate_provider(self):
        """Test registering duplicate provider."""
        registry = ProviderRegistry()
        provider = SingletonProvider("test", lambda: TestService())

        registry.register_provider(provider, LifecycleType.SINGLETON)

        # Try to register again
        with pytest.raises(ValueError, match="Provider 'test' is already registered"):
            registry.register_provider(provider, LifecycleType.SINGLETON)

    def test_register_singleton_helper(self):
        """Test register_singleton helper method."""
        registry = ProviderRegistry()

        provider = registry.register_singleton("test", lambda: TestService())

        assert isinstance(provider, SingletonProvider)
        assert registry.has_provider("test")

    def test_register_factory_helper(self):
        """Test register_factory helper method."""
        registry = ProviderRegistry()

        provider = registry.register_factory("test", lambda: TestService())

        assert isinstance(provider, FactoryProvider)
        assert registry.has_provider("test")

    def test_register_prototype_helper(self):
        """Test register_prototype helper method."""
        registry = ProviderRegistry()
        prototype = TestPrototypeService(42)

        provider = registry.register_prototype("test", prototype)

        assert isinstance(provider, PrototypeProvider)
        assert registry.has_provider("test")

    def test_register_class_helper(self):
        """Test register_class helper method."""
        registry = ProviderRegistry()

        provider = registry.register_class("test", TestService)

        assert isinstance(provider, ClassProvider)
        assert registry.has_provider("test")

    def test_unregister_provider(self):
        """Test unregistering a provider."""
        registry = ProviderRegistry()
        registry.register_singleton("test", lambda: TestService())

        assert registry.has_provider("test")

        registry.unregister_provider("test")

        assert not registry.has_provider("test")
        assert registry.get_provider_count() == 0

    def test_unregister_nonexistent_provider(self):
        """Test unregistering non-existent provider."""
        registry = ProviderRegistry()

        with pytest.raises(
            ValueError, match="Provider 'nonexistent' is not registered"
        ):
            registry.unregister_provider("nonexistent")

    def test_get_instance(self):
        """Test getting instances from registry."""
        registry = ProviderRegistry()
        registry.register_singleton("test", lambda: TestService("registry_test"))

        instance = registry.get("test")
        assert isinstance(instance, TestService)
        assert instance.name == "registry_test"

    def test_get_nonexistent_provider(self):
        """Test getting from non-existent provider."""
        registry = ProviderRegistry()

        with pytest.raises(
            DependencyResolutionError,
            match="Provider 'nonexistent' is not registered",
        ):
            registry.get("nonexistent")

    def test_dependency_resolution(self):
        """Test automatic dependency resolution."""
        registry = ProviderRegistry()

        # Register dependencies in reverse order
        registry.register_class("dependent", TestDependentService)
        registry.register_singleton("service", lambda: TestService("dependency"))

        # Get dependent service - should auto-resolve dependencies
        instance = registry.get("dependent")
        assert isinstance(instance, TestDependentService)
        assert instance.service.name == "dependency"

    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        registry = ProviderRegistry()

        # Create circular dependency
        deps_a = [Dependency("service_b", str, required=True)]
        deps_b = [Dependency("service_a", str, required=True)]

        registry.register_factory(
            "service_a", lambda service_b: f"A depends on {service_b}", deps_a
        )
        registry.register_factory(
            "service_b", lambda service_a: f"B depends on {service_a}", deps_b
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            registry.get("service_a")

        assert "service_a" in str(exc_info.value)
        assert "service_b" in str(exc_info.value)

    def test_dependency_graph(self):
        """Test dependency graph generation."""
        registry = ProviderRegistry()

        # Register services with dependencies
        registry.register_class("complex", MockComplexService)
        registry.register_class("dependent", MockDependentService)
        registry.register_singleton("service", lambda: MockService())

        graph = registry.get_dependency_graph()

        assert "service" in graph
        assert "dependent" in graph
        assert "complex" in graph

        # Check dependencies - complex depends on service and dependent
        assert "service" in graph["complex"]
        assert "dependent" in graph["complex"]
        # dependent depends on service
        assert "service" in graph["dependent"]

    def test_validate_dependencies(self):
        """Test dependency validation."""
        registry = ProviderRegistry()

        # Register service with missing dependency
        deps = [Dependency("missing_service", MockService, required=True)]
        registry.register_factory("broken", lambda missing_service: MockService(), deps)

        errors = registry.validate_dependencies()
        assert len(errors) > 0
        assert "missing required dependency 'missing_service'" in errors[0]

    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = ProviderRegistry()

        registry.register_singleton("test1", lambda: MockService())
        registry.register_factory("test2", lambda: MockService())

        assert registry.get_provider_count() == 2

        registry.clear()

        assert registry.get_provider_count() == 0
        assert registry.get_provider_names() == []

    def test_thread_safety(self):
        """Test thread safety of provider registry."""
        registry = ProviderRegistry()
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
        registry = ProviderRegistry()

        # Register services to match parameter names of MockComplexService (service, dependent, config)
        registry.register_class("complex", MockComplexService)
        registry.register_singleton("service", lambda: MockService("main_service"))
        registry.register_class("dependent", MockDependentService)

        # Get complex service - should resolve all dependencies
        instance = registry.get("complex", config="custom")

        assert isinstance(instance, MockComplexService)
        assert isinstance(instance.service, MockService)
        assert isinstance(instance.dependent, MockDependentService)
        assert instance.config == "custom"
        assert instance.service.name == "main_service"
        assert (
            instance.dependent.service.name == "main_service"
        )  # dependent also gets the same service

    def test_mixed_lifecycle_scenario(self):
        """Test scenario with mixed lifecycle types."""
        registry = ProviderRegistry()

        # Singleton base service
        registry.register_singleton("base", lambda: TestService("base"))

        # Register provider that matches parameter name 'service' for TestDependentService
        registry.register_singleton("service", lambda: TestService("shared"))

        # Factory service that depends on singleton
        registry.register_class("factory_service", TestDependentService)

        # Prototype service
        prototype = TestPrototypeService(100)
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
        registry = ProviderRegistry()

        # Register initial provider
        registry.register_singleton("service", lambda: TestService("original"))

        original_instance = registry.get("service")
        assert original_instance.name == "original"

        # Replace provider
        registry.unregister_provider("service")
        registry.register_singleton("service", lambda: TestService("replacement"))

        new_instance = registry.get("service")
        assert new_instance.name == "replacement"
        assert new_instance is not original_instance
