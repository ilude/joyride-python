"""
Tests for Joyride Configuration Management System

This module tests hierarchical configuration loading, validation, and management
for the Joyride DNS Service dependency injection container.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.joyride.injection.config import (
    Config,
    ConfigLoader,
    ConfigSchema,
    ConfigSource,
    ConfigValidator,
    create_config,
)


class TestConfigSource:
    """Test configuration source functionality."""

    def test_config_source_creation(self):
        """Test creating a configuration source."""
        data = {"key": "value"}
        source = ConfigSource(name="test", priority=10, data=data, source_type="test")

        assert source.name == "test"
        assert source.priority == 10
        assert source.data == data
        assert source.source_type == "test"
        assert source.metadata == {}

    def test_config_source_with_metadata(self):
        """Test configuration source with metadata."""
        metadata = {"version": "1.0", "author": "test"}
        source = ConfigSource(
            name="test",
            priority=10,
            data={"key": "value"},
            source_type="test",
            metadata=metadata,
        )

        assert source.metadata == metadata

    def test_config_source_validation(self):
        """Test configuration source validation."""
        # Invalid data type
        with pytest.raises(ValueError, match="Configuration data must be a dictionary"):
            ConfigSource(
                name="test", priority=10, data="not a dict", source_type="test"
            )

        # Invalid priority type
        with pytest.raises(ValueError, match="Priority must be an integer"):
            ConfigSource(
                name="test", priority="not an int", data={}, source_type="test"
            )


class TestConfigSchema:
    """Test configuration schema functionality."""

    def test_schema_creation(self):
        """Test creating a configuration schema."""
        schema = ConfigSchema(
            required_keys=["required_key"],
            optional_keys=["optional_key"],
            key_types={"required_key": str},
            validators={"required_key": lambda x: len(x) > 0},
        )

        assert "required_key" in schema.required_keys
        assert "optional_key" in schema.optional_keys
        assert schema.key_types["required_key"] == str
        assert "required_key" in schema.validators

    def test_key_validation_type_checking(self):
        """Test key validation with type checking."""
        schema = ConfigSchema(key_types={"port": int, "host": str})

        # Valid types
        assert schema.validate_key("port", 8080) is True
        assert schema.validate_key("host", "localhost") is True

        # Invalid types
        with pytest.raises(ValueError, match="Key 'port' must be of type int"):
            schema.validate_key("port", "8080")

        with pytest.raises(ValueError, match="Key 'host' must be of type str"):
            schema.validate_key("host", 8080)

    def test_key_validation_custom_validators(self):
        """Test key validation with custom validators."""
        schema = ConfigSchema(
            validators={"port": lambda x: 1 <= x <= 65535, "name": lambda x: len(x) > 0}
        )

        # Valid values
        assert schema.validate_key("port", 8080) is True
        assert schema.validate_key("name", "test") is True

        # Invalid values
        with pytest.raises(ValueError, match="Key 'port' failed custom validation"):
            schema.validate_key("port", 70000)

        with pytest.raises(ValueError, match="Key 'name' failed custom validation"):
            schema.validate_key("name", "")

    def test_schema_validation_required_keys(self):
        """Test schema validation for required keys."""
        schema = ConfigSchema(required_keys=["host", "port"])

        # Valid configuration
        config = {"host": "localhost", "port": 8080}
        assert schema.validate(config) is True

        # Missing required key
        config = {"host": "localhost"}
        with pytest.raises(
            ValueError, match="Required configuration key 'port' is missing"
        ):
            schema.validate(config)

    def test_schema_validation_unknown_keys(self):
        """Test schema validation for unknown keys."""
        schema = ConfigSchema(required_keys=["host"], optional_keys=["port"])

        # Valid configuration
        config = {"host": "localhost", "port": 8080}
        assert schema.validate(config) is True

        # Unknown key
        config = {"host": "localhost", "unknown": "value"}
        with pytest.raises(ValueError, match="Unknown configuration key 'unknown'"):
            schema.validate(config)

    def test_schema_validation_nested(self):
        """Test schema validation for nested configurations."""
        nested_schema = ConfigSchema(
            required_keys=["enabled"], key_types={"enabled": bool}
        )

        schema = ConfigSchema(
            required_keys=["service"], nested_schemas={"service": nested_schema}
        )

        # Valid nested configuration
        config = {"service": {"enabled": True}}
        assert schema.validate(config) is True

        # Invalid nested configuration - wrong type
        config = {"service": {"enabled": "yes"}}
        with pytest.raises(ValueError, match="Key 'enabled' must be of type bool"):
            schema.validate(config)

        # Invalid nested configuration - not a dict
        config = {"service": "not a dict"}
        with pytest.raises(
            ValueError, match="Nested configuration 'service' must be a dictionary"
        ):
            schema.validate(config)


class TestConfigLoader:
    """Test configuration loader functionality."""

    def test_loader_creation(self):
        """Test creating a configuration loader."""
        loader = ConfigLoader()
        assert loader.sources == []
        assert loader._env_prefix == "JOYRIDE_"

    def test_add_source(self):
        """Test adding configuration sources."""
        loader = ConfigLoader()

        source1 = ConfigSource("test1", 10, {}, "test")
        source2 = ConfigSource("test2", 20, {}, "test")

        loader.add_source(source1)
        loader.add_source(source2)

        # Should be sorted by priority (highest first)
        assert len(loader.sources) == 2
        assert loader.sources[0].priority == 20
        assert loader.sources[1].priority == 10

    def test_add_source_validation(self):
        """Test validation when adding sources."""
        loader = ConfigLoader()

        with pytest.raises(ValueError, match="Source must be a ConfigSource instance"):
            loader.add_source("not a source")

    @patch.dict(
        os.environ,
        {
            "JOYRIDE_DNS_PORT": "8053",
            "JOYRIDE_DNS_HOST": "localhost",
            "JOYRIDE_LOGGING_LEVEL": "DEBUG",
            "JOYRIDE_ENABLED": "true",
        },
    )
    def test_load_from_environment(self):
        """Test loading configuration from environment variables."""
        loader = ConfigLoader()
        source = loader.load_from_environment()

        assert source.name == "environment"
        assert source.priority == 100
        assert source.source_type == "env"

        # Check nested structure
        assert source.data["dns"]["port"] == 8053
        assert source.data["dns"]["host"] == "localhost"
        assert source.data["logging"]["level"] == "DEBUG"
        assert source.data["enabled"] is True

    @patch.dict(
        os.environ, {"TEST_KEY": "value", "TEST_NUMERIC": "42", "TEST_BOOL": "false"}
    )
    def test_load_from_environment_custom_prefix(self):
        """Test loading from environment with custom prefix."""
        loader = ConfigLoader()
        source = loader.load_from_environment("TEST_")

        assert source.data["key"] == "value"
        assert source.data["numeric"] == 42
        assert source.data["bool"] is False

    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        config_data = {
            "dns": {"port": 8053, "host": "localhost"},
            "logging": {"level": "DEBUG"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config_data, f)
            yaml_file = f.name

        try:
            loader = ConfigLoader()
            source = loader.load_from_file(yaml_file, priority=75)

            assert source.name == f"file:{Path(yaml_file).name}"
            assert source.priority == 75
            assert source.source_type == "file"
            assert source.data == config_data
            assert source.metadata["format"] == ".yaml"
        finally:
            os.unlink(yaml_file)

    def test_load_from_json_file(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "dns": {"port": 8053, "host": "localhost"},
            "logging": {"level": "DEBUG"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            json_file = f.name

        try:
            loader = ConfigLoader()
            source = loader.load_from_file(json_file, priority=75)

            assert source.name == f"file:{Path(json_file).name}"
            assert source.priority == 75
            assert source.source_type == "file"
            assert source.data == config_data
            assert source.metadata["format"] == ".json"
        finally:
            os.unlink(json_file)

    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file."""
        loader = ConfigLoader()

        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            loader.load_from_file("/nonexistent/config.yaml")

    def test_load_from_unsupported_file(self):
        """Test loading from unsupported file format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("not a config file")
            txt_file = f.name

        try:
            loader = ConfigLoader()
            with pytest.raises(ValueError, match="Unsupported file format"):
                loader.load_from_file(txt_file)
        finally:
            os.unlink(txt_file)

    def test_load_defaults(self):
        """Test loading default configuration."""
        loader = ConfigLoader()
        source = loader.load_defaults()

        assert source.name == "defaults"
        assert source.priority == 0
        assert source.source_type == "default"

        # Check some expected defaults
        assert source.data["dns"]["port"] == 53
        assert source.data["dns"]["host"] == "0.0.0.0"
        assert source.data["docker"]["socket"] == "unix:///var/run/docker.sock"
        assert source.data["swim"]["port"] == 7777

    def test_merge_sources(self):
        """Test merging configuration sources."""
        loader = ConfigLoader()

        # Add sources with different priorities
        defaults = ConfigSource(
            "defaults",
            0,
            {"dns": {"port": 53, "host": "0.0.0.0"}, "logging": {"level": "INFO"}},
            "default",
        )

        file_config = ConfigSource(
            "file",
            50,
            {
                "dns": {"port": 8053},  # Override port
                "docker": {"socket": "tcp://localhost:2376"},  # New key
            },
            "file",
        )

        env_config = ConfigSource(
            "env", 100, {"logging": {"level": "DEBUG"}}, "env"  # Override logging level
        )

        loader.add_source(defaults)
        loader.add_source(file_config)
        loader.add_source(env_config)

        merged = loader.merge_sources()

        # Environment should override file, file should override defaults
        assert merged["dns"]["port"] == 8053  # From file
        assert merged["dns"]["host"] == "0.0.0.0"  # From defaults
        assert merged["logging"]["level"] == "DEBUG"  # From environment
        assert merged["docker"]["socket"] == "tcp://localhost:2376"  # From file

    def test_parse_env_value_types(self):
        """Test parsing environment variable values to correct types."""
        loader = ConfigLoader()

        # Boolean values
        assert loader._parse_env_value("true") is True
        assert loader._parse_env_value("false") is False
        assert loader._parse_env_value("yes") is True
        assert loader._parse_env_value("no") is False
        assert loader._parse_env_value("1") is True
        assert loader._parse_env_value("0") is False

        # Numeric values
        assert loader._parse_env_value("42") == 42
        assert loader._parse_env_value("3.14") == 3.14

        # JSON values
        assert loader._parse_env_value('["item1", "item2"]') == ["item1", "item2"]
        assert loader._parse_env_value('{"key": "value"}') == {"key": "value"}

        # String values
        assert loader._parse_env_value("plain_string") == "plain_string"


class TestConfigValidator:
    """Test configuration validator functionality."""

    def test_validator_creation(self):
        """Test creating a configuration validator."""
        schema = ConfigSchema()
        validator = ConfigValidator(schema)
        assert validator.schema == schema

    def test_validator_default_schema(self):
        """Test validator with default schema."""
        validator = ConfigValidator()
        assert validator.schema is not None

        # Test with valid DNS configuration
        config = {"dns": {"port": 8053, "host": "localhost"}}
        assert validator.validate(config) is True

        # Test with invalid DNS configuration
        config = {"dns": {"port": 70000, "host": "localhost"}}  # Invalid port
        with pytest.raises(ValueError, match="Configuration validation failed"):
            validator.validate(config)

    def test_validator_custom_schema(self):
        """Test validator with custom schema."""
        schema = ConfigSchema(required_keys=["service"], key_types={"service": str})

        validator = ConfigValidator(schema)

        # Valid configuration
        config = {"service": "dns"}
        assert validator.validate(config) is True

        # Invalid configuration
        config = {}  # Missing required key
        with pytest.raises(ValueError, match="Configuration validation failed"):
            validator.validate(config)


class TestConfig:
    """Test main configuration class functionality."""

    def test_config_creation(self):
        """Test creating a configuration instance."""
        data = {"dns": {"port": 8053, "host": "localhost"}}
        config = Config(data=data)

        assert config.data == data
        assert config.sources == []
        assert config.schema is None

    def test_config_with_validation(self):
        """Test configuration with schema validation."""
        schema = ConfigSchema(
            required_keys=["dns"],
            nested_schemas={
                "dns": ConfigSchema(
                    required_keys=["port", "host"], key_types={"port": int, "host": str}
                )
            },
        )

        # Valid configuration
        data = {"dns": {"port": 8053, "host": "localhost"}}
        config = Config(data=data, schema=schema)
        assert config.data == data

        # Invalid configuration
        data = {"dns": {"port": "invalid", "host": "localhost"}}
        with pytest.raises(ValueError):
            Config(data=data, schema=schema)

    def test_config_get_method(self):
        """Test getting configuration values."""
        data = {
            "dns": {"port": 8053, "host": "localhost"},
            "logging": {"level": "DEBUG"},
        }
        config = Config(data=data)

        # Simple key access
        assert config.get("dns.port") == 8053
        assert config.get("dns.host") == "localhost"
        assert config.get("logging.level") == "DEBUG"

        # Non-existent key
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"
        assert config.get("dns.nonexistent") is None

    def test_config_set_method(self):
        """Test setting configuration values."""
        config = Config(data={})

        # Set nested values
        config.set("dns.port", 8053)
        config.set("dns.host", "localhost")
        config.set("logging.level", "DEBUG")

        assert config.data["dns"]["port"] == 8053
        assert config.data["dns"]["host"] == "localhost"
        assert config.data["logging"]["level"] == "DEBUG"

    def test_config_update_method(self):
        """Test updating configuration."""
        config = Config(data={"dns": {"port": 53}})

        updates = {"dns": {"host": "localhost"}, "logging": {"level": "DEBUG"}}
        config.update(updates)

        assert config.data["dns"]["host"] == "localhost"
        assert config.data["logging"]["level"] == "DEBUG"
        assert config.data["dns"]["port"] == 53  # Should preserve existing

    def test_config_dictionary_access(self):
        """Test dictionary-style access."""
        data = {"dns": {"port": 8053, "host": "localhost"}}
        config = Config(data=data)

        # Get
        assert config["dns.port"] == 8053
        assert config["dns.host"] == "localhost"

        # Set
        config["dns.ttl"] = 300
        assert config.data["dns"]["ttl"] == 300

        # Contains
        assert "dns.port" in config
        assert "nonexistent" not in config


class TestCreateConfig:
    """Test configuration creation helper function."""

    @patch.dict(os.environ, {"JOYRIDE_DNS_PORT": "8053"})
    def test_create_config_defaults_only(self):
        """Test creating configuration with defaults only."""
        config = create_config()

        # Should have defaults
        assert config.get("dns.port") == 8053  # Environment override
        assert config.get("dns.host") == "0.0.0.0"  # Default
        assert config.get("docker.socket") == "unix:///var/run/docker.sock"  # Default

        # Should have multiple sources
        assert len(config.sources) >= 2  # defaults + environment

    def test_create_config_with_files(self):
        """Test creating configuration with file sources."""
        config_data = {"dns": {"port": 9053, "host": "custom.host"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config_data, f)
            yaml_file = f.name

        try:
            config = create_config(config_files=[yaml_file])

            # File should override defaults
            assert config.get("dns.port") == 9053
            assert config.get("dns.host") == "custom.host"

            # Should still have defaults for other values
            assert config.get("docker.socket") == "unix:///var/run/docker.sock"
        finally:
            os.unlink(yaml_file)

    @patch.dict(os.environ, {"TEST_DNS_PORT": "7053"})
    def test_create_config_custom_prefix(self):
        """Test creating configuration with custom environment prefix."""
        config = create_config(env_prefix="TEST_")

        assert config.get("dns.port") == 7053

    def test_create_config_no_defaults(self):
        """Test creating configuration without defaults."""
        config = create_config(include_defaults=False)

        # Should not have default values
        assert config.get("dns.port") is None
        assert config.get("docker.socket") is None

    def test_create_config_with_schema(self):
        """Test creating configuration with validation schema."""
        schema = ConfigSchema(
            required_keys=["dns"],
            optional_keys=[
                "docker",
                "swim",
                "hosts",
                "logging",
                "events",
            ],  # Allow other default keys
            nested_schemas={
                "dns": ConfigSchema(
                    required_keys=["port"],
                    optional_keys=[
                        "host",
                        "ttl",
                        "backend",
                    ],  # Allow other DNS default keys
                    key_types={"port": int, "host": str, "ttl": int, "backend": str},
                )
            },
        )

        # Should work with valid defaults
        config = create_config(schema=schema)
        assert config.schema == schema
        assert config.get("dns.port") == 53  # Default port
