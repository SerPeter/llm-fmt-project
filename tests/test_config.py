"""Tests for configuration file support."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from llm_fmt.cli import main
from llm_fmt.config import (
    CONFIG_FILENAME,
    Config,
    FilterConfig,
    OutputConfig,
    find_config_file,
    load_config,
)
from llm_fmt.errors import ConfigError


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_config(self) -> None:
        """Default config has expected values."""
        config = Config.default()
        assert config.format == "auto"
        assert config.tokenizer == "cl100k_base"
        assert config.filter.default_exclude == []
        assert config.filter.default_max_depth is None
        assert config.output.color is True

    def test_config_with_custom_values(self) -> None:
        """Config can be created with custom values."""
        config = Config(
            format="toon",
            tokenizer="o200k_base",
            filter=FilterConfig(default_exclude=["_meta"], default_max_depth=3),
            output=OutputConfig(color=False),
        )
        assert config.format == "toon"
        assert config.tokenizer == "o200k_base"
        assert config.filter.default_exclude == ["_meta"]
        assert config.filter.default_max_depth == 3
        assert config.output.color is False


class TestFindConfigFile:
    """Tests for find_config_file function."""

    def test_find_in_current_dir(self, tmp_path: Path) -> None:
        """Config file found in current directory."""
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text("[defaults]\n")

        result = find_config_file(start_dir=tmp_path)
        assert result == config_file

    def test_find_in_home_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config file found in home directory when not in current."""
        # Create temp "home" directory with config
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        home_config = fake_home / CONFIG_FILENAME
        home_config.write_text("[defaults]\n")

        # Mock Path.home() to return our fake home
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Search from a directory without config
        search_dir = tmp_path / "work"
        search_dir.mkdir()

        result = find_config_file(start_dir=search_dir)
        assert result == home_config

    def test_current_dir_takes_precedence(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Current directory config takes precedence over home."""
        # Create config in both locations
        current_config = tmp_path / CONFIG_FILENAME
        current_config.write_text('[defaults]\nformat = "toon"\n')

        fake_home = tmp_path / "home"
        fake_home.mkdir()
        home_config = fake_home / CONFIG_FILENAME
        home_config.write_text('[defaults]\nformat = "yaml"\n')

        monkeypatch.setattr(Path, "home", lambda: fake_home)

        result = find_config_file(start_dir=tmp_path)
        assert result == current_config

    def test_no_config_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns None when no config file exists."""
        # Mock home to a directory without config
        fake_home = tmp_path / "empty_home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        result = find_config_file(start_dir=tmp_path)
        assert result is None


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, tmp_path: Path) -> None:
        """Load valid TOML config file."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[defaults]
format = "toon"
tokenizer = "o200k_base"

[filter]
default_exclude = ["_meta", "_links"]
default_max_depth = 5

[output]
color = false
""")

        config = load_config(config_file)
        assert config.format == "toon"
        assert config.tokenizer == "o200k_base"
        assert config.filter.default_exclude == ["_meta", "_links"]
        assert config.filter.default_max_depth == 5
        assert config.output.color is False

    def test_load_partial_config(self, tmp_path: Path) -> None:
        """Load config with only some settings."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[defaults]
format = "yaml"
""")

        config = load_config(config_file)
        assert config.format == "yaml"
        # Other values should be defaults
        assert config.tokenizer == "cl100k_base"
        assert config.filter.default_exclude == []
        assert config.output.color is True

    def test_load_empty_config(self, tmp_path: Path) -> None:
        """Empty config file returns defaults."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("")

        config = load_config(config_file)
        assert config.format == "auto"
        assert config.tokenizer == "cl100k_base"

    def test_load_no_config_returns_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No config file returns defaults."""
        # Mock home to empty directory
        fake_home = tmp_path / "empty_home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Change to tmp_path to avoid picking up real config
        monkeypatch.chdir(tmp_path)

        config = load_config()
        assert config.format == "auto"
        assert config.tokenizer == "cl100k_base"

    def test_load_missing_explicit_file_raises(self, tmp_path: Path) -> None:
        """Explicit config path that doesn't exist raises error."""
        missing = tmp_path / "missing.toml"

        with pytest.raises(ConfigError, match="Config file not found"):
            load_config(missing)

    def test_load_invalid_toml_raises(self, tmp_path: Path) -> None:
        """Invalid TOML syntax raises error."""
        config_file = tmp_path / "bad.toml"
        config_file.write_text("this is not valid { toml }")

        with pytest.raises(ConfigError, match="Invalid TOML"):
            load_config(config_file)

    def test_invalid_exclude_type_raises(self, tmp_path: Path) -> None:
        """Non-list default_exclude raises error."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[filter]
default_exclude = "not_a_list"
""")

        with pytest.raises(ConfigError, match="must be a list"):
            load_config(config_file)

    def test_invalid_max_depth_type_raises(self, tmp_path: Path) -> None:
        """Non-integer max_depth raises error."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[filter]
default_max_depth = "five"
""")

        with pytest.raises(ConfigError, match="must be a non-negative integer"):
            load_config(config_file)

    def test_negative_max_depth_raises(self, tmp_path: Path) -> None:
        """Negative max_depth raises error."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[filter]
default_max_depth = -1
""")

        with pytest.raises(ConfigError, match="must be a non-negative integer"):
            load_config(config_file)


class TestCLIConfigIntegration:
    """Tests for CLI config file integration."""

    def test_cli_uses_config_format(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI uses format from config file."""
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text('[defaults]\nformat = "yaml"\n')

        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, input='{"key": "value"}')

        assert result.exit_code == 0
        # YAML format output
        assert "key: value" in result.output

    def test_cli_format_overrides_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLI --format overrides config file."""
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text('[defaults]\nformat = "yaml"\n')

        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["--format", "json"], input='{"key": "value"}')

        assert result.exit_code == 0
        # JSON format output (compact)
        assert '{"key":"value"}' in result.output

    def test_cli_explicit_config_path(self, tmp_path: Path) -> None:
        """CLI --config specifies explicit config path."""
        config_file = tmp_path / "custom-config.toml"
        config_file.write_text('[defaults]\nformat = "yaml"\n')

        runner = CliRunner()
        result = runner.invoke(
            main, ["--config", str(config_file)], input='{"key": "value"}'
        )

        assert result.exit_code == 0
        assert "key: value" in result.output

    def test_cli_config_max_depth(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config max_depth is applied."""
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text("""
[defaults]
format = "json"

[filter]
default_max_depth = 1
""")

        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, input='{"a": {"b": {"c": 1}}}')

        assert result.exit_code == 0
        # Depth 1 should truncate nested values
        assert '"a":' in result.output
        assert '"c"' not in result.output

    def test_cli_max_depth_overrides_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLI --max-depth overrides config."""
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text("""
[defaults]
format = "json"

[filter]
default_max_depth = 1
""")

        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["--max-depth", "3"], input='{"a": {"b": {"c": 1}}}')

        assert result.exit_code == 0
        # Full depth preserved
        assert '"c":1' in result.output

    def test_cli_no_color_overrides_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLI --no-color overrides config color=true."""
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text("""
[output]
color = true
""")

        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            main, ["--no-color", "--analyze"], input='{"key": "value"}'
        )

        assert result.exit_code == 0
        # Output should work (specific color test would need terminal)
        assert "Token Analysis" in result.output

    def test_cli_config_color_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config color=false disables colors."""
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text("""
[output]
color = false
""")

        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["--analyze"], input='{"key": "value"}')

        assert result.exit_code == 0
        assert "Token Analysis" in result.output

    def test_cli_invalid_config_error(self, tmp_path: Path) -> None:
        """CLI shows error for invalid config file."""
        bad_config = tmp_path / "bad.toml"
        bad_config.write_text("invalid { toml }")

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(bad_config)], input='{"key": "value"}')

        assert result.exit_code != 0
        assert "Invalid TOML" in result.output

    def test_cli_missing_config_error(self, tmp_path: Path) -> None:
        """CLI shows error for missing explicit config file."""
        runner = CliRunner()
        # Click's exists=True on the path option will catch this
        result = runner.invoke(
            main, ["--config", str(tmp_path / "missing.toml")], input='{"key": "value"}'
        )

        assert result.exit_code != 0

    def test_cli_help_shows_config_option(self) -> None:
        """Help shows --config option."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "--config" in result.output
        assert "-c" in result.output
