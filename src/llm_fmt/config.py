"""Configuration system for llm-fmt.

Implements hierarchical configuration with precedence:
1. CLI arguments (highest)
2. Environment variables (LLM_FMT_* prefix)
3. Dedicated config file (.llm-fmt.yaml / .llm-fmt.toml)
4. pyproject.toml [tool.llm-fmt] section
5. Strong defaults (lowest)
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Try importing yaml, but make it optional
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None


@dataclass
class LimitsConfig:
    """Resource limits to prevent context window flooding."""

    max_tokens: int = 10000
    max_items: int = 500
    max_string_length: int = 500
    max_depth: int = 8


@dataclass
class TruncationConfig:
    """Truncation behavior settings."""

    strategy: str = "head"
    show_summary: bool = True


@dataclass
class FilterConfig:
    """Default filtering settings."""

    default_exclude: list[str] = field(default_factory=list)


@dataclass
class OutputConfig:
    """Output behavior settings."""

    strict: bool = False


@dataclass
class Config:
    """Main configuration container.

    Attributes:
        format: Output format (auto, toon, json, yaml, tsv, csv).
        input_format: Input format detection mode.
        limits: Resource limits configuration.
        truncation: Truncation behavior configuration.
        filter: Default filtering configuration.
        output: Output behavior configuration.
    """

    format: str = "auto"
    input_format: str = "auto"
    limits: LimitsConfig = field(default_factory=LimitsConfig)
    truncation: TruncationConfig = field(default_factory=TruncationConfig)
    filter: FilterConfig = field(default_factory=FilterConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def load(
        cls,
        config_path: Path | None = None,
        no_config: bool = False,  # noqa: FBT001, FBT002
        start_dir: Path | None = None,
    ) -> Config:
        """Load config with full hierarchy resolution.

        Args:
            config_path: Explicit config file path (skips search).
            no_config: If True, ignore all config files, use defaults only.
            start_dir: Directory to start searching from (default: cwd).

        Returns:
            Resolved Config instance.
        """
        config = cls()

        if not no_config:
            if config_path:
                file_config = cls._load_file(config_path)
                config = cls._merge(config, file_config)
            else:
                file_config = cls._find_and_load(start_dir or Path.cwd())
                config = cls._merge(config, file_config)

        # Apply environment variables (higher priority than files)
        return cls._apply_env(config)

    @classmethod
    def _find_and_load(cls, start_dir: Path) -> dict[str, Any]:
        """Search for config files in standard locations.

        Search order:
        1. .llm-fmt.yaml / .llm-fmt.yml
        2. .llm-fmt.toml
        3. pyproject.toml [tool.llm-fmt]
        4. Walk up parent directories (stop at .git or filesystem root)
        5. ~/.config/llm-fmt/config.yaml
        """
        current = start_dir.resolve()

        while True:
            # Check for dedicated config files
            for name in [".llm-fmt.yaml", ".llm-fmt.yml"]:
                config_file = current / name
                if config_file.exists():
                    return cls._load_yaml(config_file)

            toml_file = current / ".llm-fmt.toml"
            if toml_file.exists():
                return cls._load_toml(toml_file)

            # Check pyproject.toml
            pyproject = current / "pyproject.toml"
            if pyproject.exists():
                config = cls._load_pyproject(pyproject)
                if config:
                    return config

            # Check for .git (stop searching)
            if (current / ".git").exists():
                break

            # Walk up to parent
            parent = current.parent
            if parent == current:
                # Reached filesystem root
                break
            current = parent

        # Check user config as fallback
        user_config = Path.home() / ".config" / "llm-fmt" / "config.yaml"
        if user_config.exists():
            return cls._load_yaml(user_config)

        return {}

    @classmethod
    def _load_file(cls, path: Path) -> dict[str, Any]:
        """Load a specific config file by path."""
        suffix = path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            return cls._load_yaml(path)
        if suffix == ".toml":
            if path.name == "pyproject.toml":
                return cls._load_pyproject(path) or {}
            return cls._load_toml(path)
        msg = f"Unsupported config file format: {suffix}"
        raise ValueError(msg)

    @classmethod
    def _load_yaml(cls, path: Path) -> dict[str, Any]:
        """Load YAML config file."""
        if not YAML_AVAILABLE:
            msg = "pyyaml is required for YAML config files. Install with: pip install pyyaml"
            raise ImportError(msg)
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    @classmethod
    def _load_toml(cls, path: Path) -> dict[str, Any]:
        """Load TOML config file."""
        with path.open("rb") as f:
            return tomllib.load(f)

    @classmethod
    def _load_pyproject(cls, path: Path) -> dict[str, Any] | None:
        """Load config from pyproject.toml [tool.llm-fmt] section."""
        with path.open("rb") as f:
            data = tomllib.load(f)
        tool_section = data.get("tool", {}).get("llm-fmt")
        return tool_section if isinstance(tool_section, dict) else None

    @classmethod
    def _merge(cls, base: Config, updates: dict[str, Any]) -> Config:
        """Merge config dict into Config instance."""
        if not updates:
            return base

        # Handle flat keys in pyproject.toml style
        # e.g., max_tokens at root level maps to limits.max_tokens

        # Defaults section
        defaults = updates.get("defaults", {})
        if "format" in defaults:
            base.format = defaults["format"]
        if "input_format" in defaults:
            base.input_format = defaults["input_format"]

        # Also check root level for pyproject.toml style
        if "format" in updates:
            base.format = updates["format"]
        if "input_format" in updates:
            base.input_format = updates["input_format"]

        # Limits section
        limits = updates.get("limits", {})
        # Also check root level
        if "max_tokens" in limits or "max_tokens" in updates:
            base.limits.max_tokens = limits.get("max_tokens", updates.get("max_tokens", base.limits.max_tokens))
        if "max_items" in limits or "max_items" in updates:
            base.limits.max_items = limits.get("max_items", updates.get("max_items", base.limits.max_items))
        if "max_string_length" in limits or "max_string_length" in updates:
            base.limits.max_string_length = limits.get(
                "max_string_length", updates.get("max_string_length", base.limits.max_string_length)
            )
        if "max_depth" in limits or "max_depth" in updates:
            base.limits.max_depth = limits.get("max_depth", updates.get("max_depth", base.limits.max_depth))

        # Truncation section
        truncation = updates.get("truncation", {})
        if "strategy" in truncation:
            base.truncation.strategy = truncation["strategy"]
        if "show_summary" in truncation:
            base.truncation.show_summary = truncation["show_summary"]

        # Filter section
        filter_config = updates.get("filter", {})
        if "default_exclude" in filter_config:
            base.filter.default_exclude = filter_config["default_exclude"]

        # Output section
        output = updates.get("output", {})
        if "strict" in output or "strict" in updates:
            base.output.strict = output.get("strict", updates.get("strict", base.output.strict))

        return base

    @classmethod
    def _apply_env(cls, config: Config) -> Config:
        """Apply environment variables (LLM_FMT_* prefix)."""
        env_map = {
            "LLM_FMT_FORMAT": ("format", str),
            "LLM_FMT_INPUT_FORMAT": ("input_format", str),
            "LLM_FMT_MAX_TOKENS": ("limits.max_tokens", int),
            "LLM_FMT_MAX_ITEMS": ("limits.max_items", int),
            "LLM_FMT_MAX_STRING_LENGTH": ("limits.max_string_length", int),
            "LLM_FMT_MAX_DEPTH": ("limits.max_depth", int),
            "LLM_FMT_TRUNCATION_STRATEGY": ("truncation.strategy", str),
            "LLM_FMT_SHOW_SUMMARY": ("truncation.show_summary", bool),
            "LLM_FMT_DEFAULT_EXCLUDE": ("filter.default_exclude", list),
            "LLM_FMT_STRICT": ("output.strict", bool),
        }

        for env_var, (path, type_) in env_map.items():
            value = os.environ.get(env_var)
            if value is None:
                continue

            # Parse value based on type
            parsed = cls._parse_env_value(value, type_)

            # Set the value on config
            cls._set_nested(config, path, parsed)

        return config

    @classmethod
    def _parse_env_value(cls, value: str, type_: type) -> str | int | bool | list[str]:
        """Parse environment variable value to the specified type."""
        if type_ is bool:
            return value.lower() in ("true", "1", "yes")
        if type_ is int:
            return int(value)
        if type_ is list:
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @classmethod
    def _set_nested(
        cls, config: Config, path: str, value: str | int | bool | list[str]  # noqa: FBT001
    ) -> None:
        """Set a nested attribute by dot-separated path."""
        parts = path.split(".")
        obj: object = config
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary for display."""
        return {
            "defaults": {
                "format": self.format,
                "input_format": self.input_format,
            },
            "limits": {
                "max_tokens": self.limits.max_tokens,
                "max_items": self.limits.max_items,
                "max_string_length": self.limits.max_string_length,
                "max_depth": self.limits.max_depth,
            },
            "truncation": {
                "strategy": self.truncation.strategy,
                "show_summary": self.truncation.show_summary,
            },
            "filter": {
                "default_exclude": self.filter.default_exclude,
            },
            "output": {
                "strict": self.output.strict,
            },
        }


def load_config(
    config_path: Path | None = None,
    *,
    no_config: bool = False,
    cli_overrides: dict[str, object] | None = None,
    start_dir: Path | None = None,
) -> Config:
    """Main entry point for config loading.

    Args:
        config_path: Explicit config file path (skips search).
        no_config: If True, ignore all config files, use defaults only.
        cli_overrides: CLI argument overrides (highest priority).
        start_dir: Directory to start searching from.

    Returns:
        Fully resolved Config instance.
    """
    config = Config.load(config_path, no_config, start_dir)

    if cli_overrides:
        config = _apply_cli_overrides(config, cli_overrides)

    return config


def _apply_cli_overrides(config: Config, overrides: dict[str, object]) -> Config:
    """Apply CLI argument overrides to config.

    Only applies non-None values.
    """
    for path, value in overrides.items():
        if value is None:
            continue
        # Type narrowed by the check above
        Config._set_nested(config, path, value)  # type: ignore[arg-type]  # noqa: SLF001
    return config
