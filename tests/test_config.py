"""Tests for the configuration system."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003

import pytest

from llm_fmt.config import Config, LimitsConfig, TruncationConfig, load_config


class TestDefaults:
    """Test default configuration values."""

    def test_defaults_when_no_config(self) -> None:
        """Strong defaults are applied when no config is found."""
        config = load_config(no_config=True)

        assert config.limits.max_tokens == 10000
        assert config.limits.max_items == 500
        assert config.limits.max_string_length == 500
        assert config.limits.max_depth == 8
        assert config.format == "auto"
        assert config.input_format == "auto"
        assert config.truncation.strategy == "head"
        assert config.truncation.show_summary is True
        assert config.filter.default_exclude == []
        assert config.output.strict is False

    def test_dataclass_defaults(self) -> None:
        """Direct instantiation uses defaults."""
        config = Config()

        assert isinstance(config.limits, LimitsConfig)
        assert isinstance(config.truncation, TruncationConfig)
        assert config.limits.max_tokens == 10000


class TestYamlConfig:
    """Test YAML configuration loading."""

    def test_yaml_config_loaded(self, tmp_path: Path) -> None:
        """YAML config file is loaded correctly."""
        yaml_content = """
defaults:
  format: toon
  input_format: json

limits:
  max_tokens: 8000
  max_items: 200

truncation:
  strategy: balanced
  show_summary: false

filter:
  default_exclude:
    - _metadata
    - debug

output:
  strict: true
"""
        config_file = tmp_path / ".llm-fmt.yaml"
        config_file.write_text(yaml_content)

        config = load_config(config_path=config_file)

        assert config.format == "toon"
        assert config.input_format == "json"
        assert config.limits.max_tokens == 8000
        assert config.limits.max_items == 200
        assert config.truncation.strategy == "balanced"
        assert config.truncation.show_summary is False
        assert config.filter.default_exclude == ["_metadata", "debug"]
        assert config.output.strict is True

    def test_yml_extension_supported(self, tmp_path: Path) -> None:
        """Both .yaml and .yml extensions work."""
        config_file = tmp_path / ".llm-fmt.yml"
        config_file.write_text("defaults:\n  format: yaml\n")

        config = load_config(config_path=config_file)
        assert config.format == "yaml"


class TestTomlConfig:
    """Test TOML configuration loading."""

    def test_toml_config_loaded(self, tmp_path: Path) -> None:
        """TOML config file is loaded correctly."""
        toml_content = """
[defaults]
format = "json"

[limits]
max_tokens = 5000
max_depth = 5

[output]
strict = true
"""
        config_file = tmp_path / ".llm-fmt.toml"
        config_file.write_text(toml_content)

        config = load_config(config_path=config_file)

        assert config.format == "json"
        assert config.limits.max_tokens == 5000
        assert config.limits.max_depth == 5
        assert config.output.strict is True


class TestPyprojectConfig:
    """Test pyproject.toml configuration loading."""

    def test_pyproject_tool_section_loaded(self, tmp_path: Path) -> None:
        """Config from [tool.llm-fmt] section is loaded."""
        toml_content = """
[project]
name = "test-project"

[tool.llm-fmt]
format = "tsv"
max_tokens = 3000
max_items = 100
strict = true

[tool.llm-fmt.filter]
default_exclude = ["internal", "debug"]
"""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(toml_content)

        config = load_config(config_path=config_file)

        assert config.format == "tsv"
        assert config.limits.max_tokens == 3000
        assert config.limits.max_items == 100
        assert config.output.strict is True
        assert config.filter.default_exclude == ["internal", "debug"]


class TestEnvironmentVariables:
    """Test environment variable configuration."""

    def test_env_overrides_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variables override file config."""
        yaml_content = """
limits:
  max_tokens: 8000
"""
        config_file = tmp_path / ".llm-fmt.yaml"
        config_file.write_text(yaml_content)

        monkeypatch.setenv("LLM_FMT_MAX_TOKENS", "5000")

        config = load_config(config_path=config_file)

        assert config.limits.max_tokens == 5000

    def test_env_format(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LLM_FMT_FORMAT sets output format."""
        monkeypatch.setenv("LLM_FMT_FORMAT", "yaml")

        config = load_config(no_config=True)

        assert config.format == "yaml"

    def test_env_strict_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LLM_FMT_STRICT=true enables strict mode."""
        monkeypatch.setenv("LLM_FMT_STRICT", "true")

        config = load_config(no_config=True)

        assert config.output.strict is True

    def test_env_strict_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LLM_FMT_STRICT=false disables strict mode."""
        monkeypatch.setenv("LLM_FMT_STRICT", "false")

        config = load_config(no_config=True)

        assert config.output.strict is False

    def test_env_boolean_variations(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Boolean env vars accept 1, yes, true."""
        for value in ["1", "yes", "TRUE", "True"]:
            monkeypatch.setenv("LLM_FMT_STRICT", value)
            config = load_config(no_config=True)
            assert config.output.strict is True, f"Failed for value: {value}"

    def test_env_default_exclude(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LLM_FMT_DEFAULT_EXCLUDE sets exclusion list."""
        monkeypatch.setenv("LLM_FMT_DEFAULT_EXCLUDE", "_metadata,_links,debug")

        config = load_config(no_config=True)

        assert config.filter.default_exclude == ["_metadata", "_links", "debug"]


class TestCliOverrides:
    """Test CLI argument overrides."""

    def test_cli_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI arguments override environment variables."""
        monkeypatch.setenv("LLM_FMT_MAX_TOKENS", "5000")

        config = load_config(
            no_config=True,
            cli_overrides={"limits.max_tokens": 3000},
        )

        assert config.limits.max_tokens == 3000

    def test_cli_overrides_file(self, tmp_path: Path) -> None:
        """CLI arguments override file config."""
        yaml_content = """
limits:
  max_tokens: 8000
output:
  strict: false
"""
        config_file = tmp_path / ".llm-fmt.yaml"
        config_file.write_text(yaml_content)

        config = load_config(
            config_path=config_file,
            cli_overrides={
                "limits.max_tokens": 2000,
                "output.strict": True,
            },
        )

        assert config.limits.max_tokens == 2000
        assert config.output.strict is True

    def test_cli_overrides_format(self) -> None:
        """CLI can override format."""
        config = load_config(
            no_config=True,
            cli_overrides={"format": "tsv"},
        )

        assert config.format == "tsv"

    def test_cli_none_values_ignored(self) -> None:
        """None values in CLI overrides don't change config."""
        config = load_config(
            no_config=True,
            cli_overrides={
                "format": None,
                "limits.max_tokens": None,
            },
        )

        # Defaults should be preserved
        assert config.format == "auto"
        assert config.limits.max_tokens == 10000


class TestConfigSearch:
    """Test configuration file search behavior."""

    def test_search_current_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config is found in current directory."""
        config_file = tmp_path / ".llm-fmt.yaml"
        config_file.write_text("limits:\n  max_tokens: 7000\n")

        monkeypatch.chdir(tmp_path)

        config = load_config()

        assert config.limits.max_tokens == 7000

    def test_search_parent_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config is found in parent directory."""
        config_file = tmp_path / ".llm-fmt.yaml"
        config_file.write_text("limits:\n  max_tokens: 6000\n")

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        config = load_config()

        assert config.limits.max_tokens == 6000

    def test_search_stops_at_git_root(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Search stops at .git directory."""
        # Create config above .git
        config_above = tmp_path / ".llm-fmt.yaml"
        config_above.write_text("limits:\n  max_tokens: 1000\n")

        # Create git repo
        git_dir = tmp_path / "repo"
        git_dir.mkdir()
        (git_dir / ".git").mkdir()

        # Create subdir in repo
        subdir = git_dir / "src"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        config = load_config()

        # Should not find config above .git, use defaults
        assert config.limits.max_tokens == 10000

    def test_yaml_has_priority_over_toml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """YAML config takes precedence over TOML when both exist."""
        yaml_file = tmp_path / ".llm-fmt.yaml"
        yaml_file.write_text("limits:\n  max_tokens: 1111\n")

        toml_file = tmp_path / ".llm-fmt.toml"
        toml_file.write_text("[limits]\nmax_tokens = 2222\n")

        monkeypatch.chdir(tmp_path)

        config = load_config()

        assert config.limits.max_tokens == 1111

    def test_dedicated_config_over_pyproject(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Dedicated config file takes precedence over pyproject.toml."""
        yaml_file = tmp_path / ".llm-fmt.yaml"
        yaml_file.write_text("limits:\n  max_tokens: 3333\n")

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.llm-fmt]\nmax_tokens = 4444\n")

        monkeypatch.chdir(tmp_path)

        config = load_config()

        assert config.limits.max_tokens == 3333


class TestNoConfig:
    """Test --no-config behavior."""

    def test_no_config_ignores_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """--no-config ignores all config files."""
        config_file = tmp_path / ".llm-fmt.yaml"
        config_file.write_text("limits:\n  max_tokens: 1000\n")

        monkeypatch.chdir(tmp_path)

        config = load_config(no_config=True)

        # Should use default, not file value
        assert config.limits.max_tokens == 10000

    def test_no_config_still_uses_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """--no-config still respects environment variables."""
        monkeypatch.setenv("LLM_FMT_MAX_TOKENS", "5000")

        config = load_config(no_config=True)

        assert config.limits.max_tokens == 5000


class TestToDict:
    """Test config serialization."""

    def test_to_dict(self) -> None:
        """Config can be serialized to dict."""
        config = Config()
        d = config.to_dict()

        assert d["defaults"]["format"] == "auto"
        assert d["limits"]["max_tokens"] == 10000
        assert d["truncation"]["strategy"] == "head"
        assert d["filter"]["default_exclude"] == []
        assert d["output"]["strict"] is False


class TestInvalidConfig:
    """Test error handling for invalid configs."""

    def test_unsupported_format(self, tmp_path: Path) -> None:
        """Unsupported config file format raises error."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"format": "toon"}')

        with pytest.raises(ValueError, match="Unsupported config file format"):
            load_config(config_path=config_file)

    def test_missing_yaml_dependency(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Clear error when pyyaml is not available."""
        import llm_fmt.config as config_module

        # Simulate pyyaml not being available
        monkeypatch.setattr(config_module, "YAML_AVAILABLE", False)

        config_file = tmp_path / ".llm-fmt.yaml"
        config_file.write_text("format: toon\n")

        with pytest.raises(ImportError, match="pyyaml is required"):
            load_config(config_path=config_file)
