"""Tests for CLI interface."""

import json

from click.testing import CliRunner

from llm_fmt.cli import main


class TestCliHelp:
    """Tests for help output."""

    def test_help(self) -> None:
        """Test --help shows usage."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Convert JSON/YAML/XML" in result.output
        assert "--format" in result.output
        assert "--output" in result.output

    def test_version(self) -> None:
        """Test --version shows version."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "llm-fmt" in result.output


class TestCliBasicConversion:
    """Tests for basic conversion."""

    def test_json_to_toon(self, tmp_path) -> None:
        """Test converting JSON file to TOON."""
        input_file = tmp_path / "test.json"
        input_file.write_text('[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]')

        runner = CliRunner()
        result = runner.invoke(main, [str(input_file)])

        assert result.exit_code == 0
        assert "id|name" in result.output
        assert "1|Alice" in result.output
        assert "2|Bob" in result.output

    def test_json_to_compact_json(self, tmp_path) -> None:
        """Test converting JSON file to compact JSON."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"key": "value", "num": 42}')

        runner = CliRunner()
        result = runner.invoke(main, [str(input_file), "-f", "json"])

        assert result.exit_code == 0
        assert result.output.strip() == '{"key":"value","num":42}'

    def test_json_to_yaml(self, tmp_path) -> None:
        """Test converting JSON file to YAML."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"name": "test", "value": 123}')

        runner = CliRunner()
        result = runner.invoke(main, [str(input_file), "-f", "yaml"])

        assert result.exit_code == 0
        assert "name: test" in result.output
        assert "value: 123" in result.output


class TestCliStdin:
    """Tests for stdin input."""

    def test_stdin_default(self) -> None:
        """Test reading from stdin when no file specified."""
        runner = CliRunner()
        result = runner.invoke(main, input='{"id": 1, "name": "test"}')

        assert result.exit_code == 0
        assert "id|name" in result.output
        assert "1|test" in result.output

    def test_stdin_explicit_dash(self) -> None:
        """Test reading from stdin with explicit -."""
        runner = CliRunner()
        result = runner.invoke(main, ["-"], input='{"key": "value"}')

        assert result.exit_code == 0


class TestCliOutputFile:
    """Tests for output file option."""

    def test_output_file(self, tmp_path) -> None:
        """Test writing to output file."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"key": "value"}')
        output_file = tmp_path / "output.toon"

        runner = CliRunner()
        result = runner.invoke(
            main, [str(input_file), "-o", str(output_file)]
        )

        assert result.exit_code == 0
        assert "Written to" in result.output
        assert output_file.exists()
        assert "key" in output_file.read_text()

    def test_output_file_json(self, tmp_path) -> None:
        """Test writing JSON to output file."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"a": 1, "b": 2}')
        output_file = tmp_path / "output.json"

        runner = CliRunner()
        result = runner.invoke(
            main, [str(input_file), "-f", "json", "-o", str(output_file)]
        )

        assert result.exit_code == 0
        content = output_file.read_text()
        parsed = json.loads(content)
        assert parsed == {"a": 1, "b": 2}


class TestCliSortKeys:
    """Tests for sort-keys option."""

    def test_sort_keys_json(self, tmp_path) -> None:
        """Test --sort-keys with JSON output."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"z": 1, "a": 2, "m": 3}')

        runner = CliRunner()
        result = runner.invoke(
            main, [str(input_file), "-f", "json", "--sort-keys"]
        )

        assert result.exit_code == 0
        assert result.output.strip() == '{"a":2,"m":3,"z":1}'

    def test_sort_keys_nested(self, tmp_path) -> None:
        """Test --sort-keys with nested objects."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"z": {"c": 1, "a": 2}, "a": 0}')

        runner = CliRunner()
        result = runner.invoke(
            main, [str(input_file), "-f", "json", "--sort-keys"]
        )

        assert result.exit_code == 0
        assert result.output.strip() == '{"a":0,"z":{"a":2,"c":1}}'


class TestCliErrors:
    """Tests for error handling."""

    def test_file_not_found(self, tmp_path) -> None:
        """Test error when file doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_path / "nonexistent.json")])

        assert result.exit_code != 0
        assert "File not found" in result.output

    def test_invalid_json(self, tmp_path) -> None:
        """Test error on invalid JSON."""
        input_file = tmp_path / "test.json"
        input_file.write_text("{invalid json}")

        runner = CliRunner()
        result = runner.invoke(main, [str(input_file)])

        assert result.exit_code != 0
        assert "Parse error" in result.output or "Error" in result.output


class TestCliInputFormat:
    """Tests for input format option."""

    def test_explicit_json_format(self, tmp_path) -> None:
        """Test explicit JSON input format."""
        input_file = tmp_path / "data.txt"  # No JSON extension
        input_file.write_text('{"key": "value"}')

        runner = CliRunner()
        result = runner.invoke(main, [str(input_file), "-F", "json"])

        assert result.exit_code == 0
        assert "key" in result.output

    def test_explicit_yaml_format(self, tmp_path) -> None:
        """Test explicit YAML input format."""
        input_file = tmp_path / "data.txt"
        input_file.write_text("key: value\nnum: 42")

        runner = CliRunner()
        result = runner.invoke(main, [str(input_file), "-F", "yaml"])

        assert result.exit_code == 0


class TestCliFilters:
    """Tests for filter options.

    Note: Filter functionality is tested in filter-specific tests.
    These tests verify the CLI accepts the filter options.
    """

    def test_filter_option_accepted(self, tmp_path) -> None:
        """Test --filter option is accepted."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"users": [{"id": 1}], "config": {"x": 1}}')

        runner = CliRunner()
        result = runner.invoke(
            main, [str(input_file), "-f", "json", "--filter", "users"]
        )

        # Filter option is accepted, conversion succeeds
        assert result.exit_code == 0

    def test_exclude_option_accepted(self, tmp_path) -> None:
        """Test --exclude option is accepted."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"keep": 1, "remove": 2}')

        runner = CliRunner()
        result = runner.invoke(
            main, [str(input_file), "-f", "json", "--exclude", "remove"]
        )

        assert result.exit_code == 0

    def test_max_depth_option_accepted(self, tmp_path) -> None:
        """Test --max-depth option is accepted."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"a": {"b": {"c": 1}}}')

        runner = CliRunner()
        result = runner.invoke(
            main, [str(input_file), "-f", "json", "--max-depth", "1"]
        )

        assert result.exit_code == 0


class TestCliNoColor:
    """Tests for --no-color option."""

    def test_no_color_accepted(self, tmp_path) -> None:
        """Test --no-color option is accepted."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"key": "value"}')

        runner = CliRunner()
        result = runner.invoke(main, [str(input_file), "--no-color"])

        assert result.exit_code == 0
