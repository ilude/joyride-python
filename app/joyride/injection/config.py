"""
Configuration Management for Joyride Dependency Injection Container

This module provides hierarchical configuration loading, validation, and management
for the Joyride DNS Service. It supports multiple configuration sources with
proper precedence and validation.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

import yaml


@dataclass
class JoyrideConfigSource:
    """Represents a configuration source with priority and metadata."""

    name: str
    priority: int  # Higher number = higher priority
    data: Dict[str, Any]
    source_type: str  # "env", "file", "default", "override"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration source after initialization."""
        if not isinstance(self.data, dict):
            raise ValueError(
                f"Configuration data must be a dictionary, got {type(self.data)}"
            )
        if not isinstance(self.priority, int):
            raise ValueError(f"Priority must be an integer, got {type(self.priority)}")


@dataclass
class JoyrideConfigSchema:
    """Configuration schema definition for validation."""

    required_keys: List[str] = field(default_factory=list)
    optional_keys: List[str] = field(default_factory=list)
    key_types: Dict[str, Type] = field(default_factory=dict)
    nested_schemas: Dict[str, "JoyrideConfigSchema"] = field(default_factory=dict)
    validators: Dict[str, callable] = field(default_factory=dict)

    def validate_key(self, key: str, value: Any) -> bool:
        """Validate a single configuration key."""
        # Type validation
        if key in self.key_types:
            expected_type = self.key_types[key]
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"Key '{key}' must be of type {expected_type.__name__}, got {type(value).__name__}"
                )

        # Custom validation
        if key in self.validators:
            validator = self.validators[key]
            if not validator(value):
                raise ValueError(f"Key '{key}' failed custom validation")

        return True

    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate entire configuration against schema."""
        # Check required keys
        for key in self.required_keys:
            if key not in config:
                raise ValueError(f"Required configuration key '{key}' is missing")

        # Validate all present keys
        for key, value in config.items():
            if key in self.required_keys or key in self.optional_keys:
                self.validate_key(key, value)
            elif key not in self.nested_schemas:
                raise ValueError(f"Unknown configuration key '{key}'")

        # Validate nested configurations
        for key, schema in self.nested_schemas.items():
            if key in config:
                if not isinstance(config[key], dict):
                    raise ValueError(
                        f"Nested configuration '{key}' must be a dictionary"
                    )
                schema.validate(config[key])

        return True


class JoyrideConfigLoader:
    """Hierarchical configuration loader supporting multiple sources."""

    def __init__(self):
        """Initialize configuration loader."""
        self.sources: List[JoyrideConfigSource] = []
        self._env_prefix = "JOYRIDE_"

    def add_source(self, source: JoyrideConfigSource) -> None:
        """Add a configuration source."""
        if not isinstance(source, JoyrideConfigSource):
            raise ValueError("Source must be a JoyrideConfigSource instance")

        self.sources.append(source)
        # Sort by priority (highest first)
        self.sources.sort(key=lambda s: s.priority, reverse=True)

    def load_from_environment(
        self, prefix: Optional[str] = None
    ) -> JoyrideConfigSource:
        """Load configuration from environment variables."""
        if prefix is None:
            prefix = self._env_prefix

        env_config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert JOYRIDE_DNS_PORT to nested structure: {"dns": {"port": value}}
                config_key = key[len(prefix) :].lower()
                self._set_nested_value(
                    env_config, config_key, self._parse_env_value(value)
                )

        return JoyrideConfigSource(
            name="environment",
            priority=100,  # High priority for environment variables
            data=env_config,
            source_type="env",
            metadata={"prefix": prefix},
        )

    def load_from_file(
        self, file_path: Union[str, Path], priority: int = 50
    ) -> JoyrideConfigSource:
        """Load configuration from YAML or JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        try:
            with path.open("r") as f:
                if path.suffix.lower() in [".yaml", ".yml"]:
                    data = yaml.safe_load(f) or {}
                elif path.suffix.lower() == ".json":
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {path.suffix}")

            return JoyrideConfigSource(
                name=f"file:{path.name}",
                priority=priority,
                data=data,
                source_type="file",
                metadata={"path": str(path), "format": path.suffix},
            )

        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to parse configuration file {path}: {e}")

    def load_defaults(self) -> JoyrideConfigSource:
        """Load default configuration values."""
        defaults = {
            "dns": {"port": 53, "host": "0.0.0.0", "ttl": 300, "backend": "memory"},
            "docker": {
                "socket": "unix:///var/run/docker.sock",
                "labels": ["joyride.enable=true"],
                "network_mode": "bridge",
            },
            "swim": {
                "port": 7777,
                "gossip_interval": 1.0,
                "probe_timeout": 0.5,
                "probe_interval": 1.0,
            },
            "hosts": {
                "directories": ["/etc/joyride/hosts"],
                "poll_interval": 5.0,
                "recursive": True,
            },
            "logging": {"level": "INFO", "format": "json", "handlers": ["console"]},
            "events": {
                "bus_type": "sync",
                "max_handlers": 10,
                "error_strategy": "log_and_continue",
            },
        }

        return JoyrideConfigSource(
            name="defaults",
            priority=0,  # Lowest priority
            data=defaults,
            source_type="default",
            metadata={"version": "1.0"},
        )

    def merge_sources(self) -> Dict[str, Any]:
        """Merge all configuration sources by priority."""
        if not self.sources:
            return {}

        # Start with lowest priority (defaults)
        merged = {}
        for source in reversed(self.sources):  # Reverse to start with lowest priority
            merged = self._deep_merge(merged, source.data)

        return merged

    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested configuration value using dot notation."""
        parts = key.split("_")
        current = config

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Boolean values
        if value.lower() in ["true", "yes", "1", "on"]:
            return True
        if value.lower() in ["false", "no", "0", "off"]:
            return False

        # Numeric values
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # JSON/YAML values (for arrays/objects)
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

        # Default to string
        return value

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result


class JoyrideConfigValidator:
    """Configuration validator with schema support."""

    def __init__(self, schema: Optional[JoyrideConfigSchema] = None):
        """Initialize validator with optional schema."""
        self.schema = schema or self._create_default_schema()

    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against schema."""
        try:
            return self.schema.validate(config)
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {e}")

    def _create_default_schema(self) -> JoyrideConfigSchema:
        """Create default configuration schema for Joyride."""
        # DNS schema
        dns_schema = JoyrideConfigSchema(
            required_keys=["port", "host"],
            optional_keys=["ttl", "backend"],
            key_types={"port": int, "host": str, "ttl": int, "backend": str},
            validators={"port": lambda x: 1 <= x <= 65535, "ttl": lambda x: x >= 0},
        )

        # Docker schema
        docker_schema = JoyrideConfigSchema(
            required_keys=["socket"],
            optional_keys=["labels", "network_mode"],
            key_types={"socket": str, "labels": list, "network_mode": str},
        )

        # SWIM schema
        swim_schema = JoyrideConfigSchema(
            required_keys=["port"],
            optional_keys=["gossip_interval", "probe_timeout", "probe_interval"],
            key_types={
                "port": int,
                "gossip_interval": float,
                "probe_timeout": float,
                "probe_interval": float,
            },
            validators={"port": lambda x: 1 <= x <= 65535},
        )

        # Hosts schema
        hosts_schema = JoyrideConfigSchema(
            required_keys=["directories"],
            optional_keys=["poll_interval", "recursive"],
            key_types={"directories": list, "poll_interval": float, "recursive": bool},
        )

        # Logging schema
        logging_schema = JoyrideConfigSchema(
            required_keys=["level"],
            optional_keys=["format", "handlers"],
            key_types={"level": str, "format": str, "handlers": list},
        )

        # Events schema
        events_schema = JoyrideConfigSchema(
            required_keys=["bus_type"],
            optional_keys=["max_handlers", "error_strategy"],
            key_types={"bus_type": str, "max_handlers": int, "error_strategy": str},
        )

        # Main schema
        return JoyrideConfigSchema(
            required_keys=[],
            optional_keys=["dns", "docker", "swim", "hosts", "logging", "events"],
            nested_schemas={
                "dns": dns_schema,
                "docker": docker_schema,
                "swim": swim_schema,
                "hosts": hosts_schema,
                "logging": logging_schema,
                "events": events_schema,
            },
        )


@dataclass
class JoyrideConfig:
    """Main configuration class for Joyride DNS Service."""

    data: Dict[str, Any]
    sources: List[JoyrideConfigSource] = field(default_factory=list)
    schema: Optional[JoyrideConfigSchema] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.schema:
            validator = JoyrideConfigValidator(self.schema)
            validator.validate(self.data)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support."""
        parts = key.split(".")
        current = self.data

        try:
            for part in parts:
                current = current[part]
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value with dot notation support."""
        parts = key.split(".")
        current = self.data

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

        # Re-validate if schema is present
        if self.schema:
            validator = JoyrideConfigValidator(self.schema)
            validator.validate(self.data)

    def update(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        # Use deep merge instead of simple update
        loader = JoyrideConfigLoader()
        self.data = loader._deep_merge(self.data, updates)

        # Re-validate if schema is present
        if self.schema:
            validator = JoyrideConfigValidator(self.schema)
            validator.validate(self.data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.data.copy()

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-style assignment."""
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration."""
        return self.get(key) is not None


def create_config(
    config_files: Optional[List[Union[str, Path]]] = None,
    env_prefix: str = "JOYRIDE_",
    include_defaults: bool = True,
    schema: Optional[JoyrideConfigSchema] = None,
) -> JoyrideConfig:
    """
    Create a complete Joyride configuration from multiple sources.

    Args:
        config_files: List of configuration files to load
        env_prefix: Prefix for environment variables
        include_defaults: Whether to include default values
        schema: Configuration schema for validation

    Returns:
        JoyrideConfig: Fully configured instance
    """
    loader = JoyrideConfigLoader()
    loader._env_prefix = env_prefix

    # Add default configuration
    if include_defaults:
        loader.add_source(loader.load_defaults())

    # Add file configurations
    if config_files:
        for i, config_file in enumerate(config_files):
            # Later files have higher priority
            priority = 50 + i
            loader.add_source(loader.load_from_file(config_file, priority))

    # Add environment configuration (highest priority)
    loader.add_source(loader.load_from_environment(env_prefix))

    # Merge and create final configuration
    merged_data = loader.merge_sources()

    return JoyrideConfig(data=merged_data, sources=loader.sources.copy(), schema=schema)
