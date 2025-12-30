"""Configuration file support for llm-fmt."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from llm_fmt.errors import ConfigError

CONFIG_FILENAME = ".llm-fmt.toml"


@dataclass
class FilterConfig:
    """Filter-related configuration."""

    default_exclude: list[str] = field(default_factory=list)
    default_max_depth: int | None = None


@dataclass
class OutputConfig:
    """Output-related configuration."""

    color: bool = True


@dataclass
class Config:
    """Configuration settings for llm-fmt."""

    format: str = "auto"
    tokenizer: str = "cl100k_base"
    filter: FilterConfig = field(default_factory=FilterConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def default(cls) -> Config:
        """Create a Config with default values."""
        return cls()


def find_config_file(start_dir: Path | None = None) -> Path | None:
    """Find configuration file in current directory or home directory.

    Args:
        start_dir: Directory to start searching from. Defaults to current directory.

    Returns:
        Path to config file if found, None otherwise.
    """
    # Check current directory first
    if start_dir is None:
        start_dir = Path.cwd()

    current_config = start_dir / CONFIG_FILENAME
    if current_config.exists():
        return current_config

    # Check home directory
    home_config = Path.home() / CONFIG_FILENAME
    if home_config.exists():
        return home_config

    return None


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file.

    Args:
        config_path: Explicit path to config file. If None, searches default locations.

    Returns:
        Loaded configuration or defaults if no config found.

    Raises:
        ConfigError: If config file exists but is invalid.
    """
    # Find config file
    if config_path is None:
        config_path = find_config_file()

    # No config file found - return defaults
    if config_path is None:
        return Config.default()

    # Config file specified but doesn't exist
    if not config_path.exists():
        msg = f"Config file not found: {config_path}"
        raise ConfigError(msg)

    # Load and parse config
    try:
        content = config_path.read_text(encoding="utf-8")
        data = tomllib.loads(content)
        return _parse_config(data)
    except tomllib.TOMLDecodeError as e:
        msg = f"Invalid TOML in config file {config_path}: {e}"
        raise ConfigError(msg) from e


def _parse_config(data: dict[str, Any]) -> Config:
    """Parse config dictionary into Config object.

    Args:
        data: Raw config dictionary from TOML.

    Returns:
        Parsed Config object.

    Raises:
        ConfigError: If config values are invalid.
    """
    config = Config.default()

    # Parse [defaults] section
    if "defaults" in data:
        defaults = data["defaults"]
        if "format" in defaults:
            config.format = str(defaults["format"])
        if "tokenizer" in defaults:
            config.tokenizer = str(defaults["tokenizer"])

    # Parse [filter] section
    if "filter" in data:
        filter_data = data["filter"]
        if "default_exclude" in filter_data:
            exclude = filter_data["default_exclude"]
            if not isinstance(exclude, list):
                msg = "filter.default_exclude must be a list"
                raise ConfigError(msg)
            config.filter.default_exclude = [str(x) for x in exclude]
        if "default_max_depth" in filter_data:
            depth = filter_data["default_max_depth"]
            if not isinstance(depth, int) or depth < 0:
                msg = "filter.default_max_depth must be a non-negative integer"
                raise ConfigError(msg)
            config.filter.default_max_depth = depth

    # Parse [output] section
    if "output" in data:
        output_data = data["output"]
        if "color" in output_data:
            config.output.color = bool(output_data["color"])

    return config
