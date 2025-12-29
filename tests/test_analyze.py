"""Tests for analysis mode."""

import json

from click.testing import CliRunner

from llm_fmt.analyze import (
    analyze,
    detect_data_shape,
    format_report,
    report_to_dict,
)
from llm_fmt.cli import main


class TestDetectDataShape:
    """Tests for detect_data_shape function."""

    def test_empty_list(self) -> None:
        """Empty list is detected correctly."""
        shape = detect_data_shape([])
        assert shape.is_array is True
        assert shape.array_length == 0
        assert "Empty array" in shape.description

    def test_uniform_array(self) -> None:
        """Uniform array of objects is detected."""
        data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        shape = detect_data_shape(data)

        assert shape.is_array is True
        assert shape.is_uniform_array is True
        assert shape.array_length == 2
        assert shape.field_count == 2
        assert "Uniform array" in shape.description

    def test_non_uniform_array(self) -> None:
        """Non-uniform array is detected."""
        data = [{"id": 1}, {"id": 2, "name": "Bob"}]
        shape = detect_data_shape(data)

        assert shape.is_array is True
        assert shape.is_uniform_array is False
        assert "varying schemas" in shape.description

    def test_primitive_array(self) -> None:
        """Array of primitives is detected."""
        data = [1, 2, 3, 4, 5]
        shape = detect_data_shape(data)

        assert shape.is_array is True
        assert shape.is_uniform_array is False
        assert shape.array_length == 5
        assert "primitives" in shape.description

    def test_flat_object(self) -> None:
        """Flat object is detected."""
        data = {"name": "test", "value": 42}
        shape = detect_data_shape(data)

        assert shape.is_array is False
        assert shape.field_count == 2
        assert "Flat object" in shape.description

    def test_nested_object(self) -> None:
        """Nested object is detected."""
        data = {"config": {"db": {"host": "localhost"}}}
        shape = detect_data_shape(data)

        assert shape.is_array is False
        assert shape.max_depth == 3
        assert "Nested object" in shape.description

    def test_depth_calculation(self) -> None:
        """Depth is calculated correctly."""
        flat_data = {"a": 1}
        nested_data = {"a": {"b": {"c": {"d": 1}}}}

        assert detect_data_shape(flat_data).max_depth == 1
        assert detect_data_shape(nested_data).max_depth == 4

    def test_mostly_primitives_true(self) -> None:
        """Mostly primitives flag works."""
        data = {"a": 1, "b": 2, "c": 3, "d": "str"}
        shape = detect_data_shape(data)
        assert shape.is_mostly_primitives is True

    def test_mostly_primitives_false(self) -> None:
        """Mostly primitives flag false for nested data."""
        data = {"a": {}, "b": {}, "c": {}, "d": 1}
        shape = detect_data_shape(data)
        assert shape.is_mostly_primitives is False

    def test_sample_keys_uniform_array(self) -> None:
        """Sample keys are captured for uniform arrays."""
        data = [{"id": 1, "name": "Alice", "age": 30}]
        shape = detect_data_shape(data)

        assert "id" in shape.sample_keys
        assert "name" in shape.sample_keys
        assert "age" in shape.sample_keys

    def test_sample_keys_flat_object(self) -> None:
        """Sample keys are captured for flat objects."""
        data = {"name": "test", "value": 42, "active": True}
        shape = detect_data_shape(data)

        assert "name" in shape.sample_keys
        assert "value" in shape.sample_keys
        assert "active" in shape.sample_keys

    def test_sample_keys_limited_to_10(self) -> None:
        """Sample keys are limited to 10 entries."""
        data = {f"field{i}": i for i in range(20)}
        shape = detect_data_shape(data)

        assert len(shape.sample_keys) == 10

    def test_large_array_sampling(self) -> None:
        """Large arrays are sampled efficiently."""
        # Create array larger than default max_sample (100)
        data = [{"id": i, "name": f"item{i}"} for i in range(500)]
        shape = detect_data_shape(data)

        # Should still detect as uniform
        assert shape.is_uniform_array is True
        assert shape.array_length == 500
        assert shape.field_count == 2

    def test_large_array_with_custom_sample(self) -> None:
        """Custom max_sample parameter works."""
        data = [{"id": i} for i in range(1000)]
        shape = detect_data_shape(data, max_sample=50)

        assert shape.is_uniform_array is True
        assert shape.array_length == 1000

    def test_sampling_detects_non_uniform_in_sample(self) -> None:
        """Non-uniform arrays detected within sample range."""
        # First 50 items uniform, then different
        uniform_part = [{"id": i, "name": f"name{i}"} for i in range(50)]
        non_uniform_part = [{"id": i, "extra": "field"} for i in range(50, 100)]
        data = uniform_part + non_uniform_part

        # With max_sample=100 (default), should detect non-uniform
        shape = detect_data_shape(data)
        assert shape.is_uniform_array is False

    def test_sampling_uniform_at_head(self) -> None:
        """If first max_sample items are uniform, detected as uniform."""
        # First 100 uniform, rest non-uniform (but not sampled)
        uniform_part = [{"id": i, "name": f"name{i}"} for i in range(100)]
        non_uniform_part = [{"id": i, "extra": "field"} for i in range(100, 200)]
        data = uniform_part + non_uniform_part

        # With max_sample=100, only samples first 100 which are uniform
        shape = detect_data_shape(data, max_sample=100)
        assert shape.is_uniform_array is True


class TestAnalyze:
    """Tests for analyze function."""

    def test_analyze_uniform_array(self) -> None:
        """Analyze uniform array recommends TOON."""
        data = [{"id": i, "name": f"item{i}"} for i in range(10)]
        report = analyze(data)

        assert report.recommendation == "TOON"
        assert any(f.name == "TOON" and f.recommended for f in report.formats)

    def test_analyze_single_object(self) -> None:
        """Analyze single object."""
        data = {"name": "test", "value": 123}
        report = analyze(data)

        # Should have all format analyses
        format_names = {f.name for f in report.formats}
        assert "Compact JSON" in format_names
        assert "YAML" in format_names
        assert "JSON (pretty)" in format_names

    def test_analyze_nested_config(self) -> None:
        """Analyze nested config object."""
        data = {"db": {"host": "localhost", "port": 5432}}
        report = analyze(data)

        # TOON is less beneficial for non-arrays
        assert report.data_shape.is_uniform_array is False

    def test_analyze_formats_sorted_by_tokens(self) -> None:
        """Formats are sorted by token count."""
        data = [{"id": 1, "name": "Alice"}]
        report = analyze(data)

        tokens = [f.tokens for f in report.formats]
        assert tokens == sorted(tokens)

    def test_analyze_savings_calculated(self) -> None:
        """Savings percentages are calculated correctly."""
        data = [{"id": i, "name": f"item{i}"} for i in range(5)]
        report = analyze(data)

        # JSON (pretty) should have 0% savings (baseline)
        baseline = next(f for f in report.formats if f.name == "JSON (pretty)")
        assert baseline.savings_percent == 0.0

        # Other formats should have positive savings
        for fmt in report.formats:
            if fmt.name != "JSON (pretty)":
                assert fmt.savings_percent >= 0 or fmt.tokens <= baseline.tokens

    def test_analyze_with_different_tokenizer(self) -> None:
        """Analyze with o200k_base tokenizer."""
        data = {"key": "value"}
        report = analyze(data, tokenizer="o200k_base")

        assert report.tokenizer == "o200k_base"
        assert report.original_tokens > 0


class TestFormatReport:
    """Tests for format_report function."""

    def test_format_report_contains_header(self) -> None:
        """Format report has header."""
        data = [{"id": 1}]
        report = analyze(data)
        output = format_report(report)

        assert "Token Analysis" in output
        assert "cl100k_base" in output

    def test_format_report_contains_formats(self) -> None:
        """Format report lists all formats."""
        data = [{"id": 1}]
        report = analyze(data)
        output = format_report(report)

        assert "TOON" in output
        assert "Compact JSON" in output
        assert "YAML" in output
        assert "JSON (pretty)" in output

    def test_format_report_shows_recommendation(self) -> None:
        """Format report shows recommendation."""
        data = [{"id": i} for i in range(10)]
        report = analyze(data)
        output = format_report(report)

        assert "recommended" in output
        assert "Recommendation:" in output

    def test_format_report_shows_data_shape(self) -> None:
        """Format report shows data shape."""
        data = [{"id": 1, "name": "Alice"}]
        report = analyze(data)
        output = format_report(report)

        assert "Data shape:" in output

    def test_format_report_shows_usage_hint(self) -> None:
        """Format report shows usage hint."""
        data = [{"id": i} for i in range(5)]
        report = analyze(data)
        output = format_report(report)

        assert "Use: llm-fmt" in output


class TestReportToDict:
    """Tests for report_to_dict function."""

    def test_report_to_dict_structure(self) -> None:
        """Report dict has expected structure."""
        data = [{"id": 1}]
        report = analyze(data)
        d = report_to_dict(report)

        assert "original_tokens" in d
        assert "tokenizer" in d
        assert "formats" in d
        assert "data_shape" in d
        assert "recommendation" in d
        assert "recommendation_reason" in d

    def test_report_to_dict_formats(self) -> None:
        """Report dict formats have correct fields."""
        data = [{"id": 1}]
        report = analyze(data)
        d = report_to_dict(report)

        for fmt in d["formats"]:
            assert "name" in fmt
            assert "tokens" in fmt
            assert "savings_percent" in fmt
            assert "recommended" in fmt

    def test_report_to_dict_data_shape(self) -> None:
        """Report dict data_shape has correct fields."""
        data = [{"id": 1}]
        report = analyze(data)
        d = report_to_dict(report)

        shape = d["data_shape"]
        assert "is_array" in shape
        assert "is_uniform_array" in shape
        assert "array_length" in shape
        assert "field_count" in shape
        assert "max_depth" in shape
        assert "description" in shape
        assert "sample_keys" in shape

    def test_report_to_dict_json_serializable(self) -> None:
        """Report dict is JSON serializable."""
        data = [{"id": i, "name": f"item{i}"} for i in range(3)]
        report = analyze(data)
        d = report_to_dict(report)

        # Should not raise
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert parsed["original_tokens"] == d["original_tokens"]


class TestAnalyzeCLI:
    """Tests for CLI --analyze option."""

    def test_analyze_cli_accepted(self) -> None:
        """Test --analyze option is accepted."""
        runner = CliRunner()
        result = runner.invoke(main, ["--analyze"], input='{"key": "value"}')

        assert result.exit_code == 0
        assert "Token Analysis" in result.output

    def test_analyze_cli_json_output(self) -> None:
        """Test --analyze --json output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--analyze", "--json"], input='[{"id": 1}]')

        assert result.exit_code == 0

        # Should be valid JSON
        data = json.loads(result.output)
        assert "original_tokens" in data
        assert "recommendation" in data

    def test_analyze_cli_with_file(self, tmp_path) -> None:
        """Test --analyze with input file."""
        input_file = tmp_path / "test.json"
        input_file.write_text('[{"id": 1, "name": "Alice"}]')

        runner = CliRunner()
        result = runner.invoke(main, [str(input_file), "--analyze"])

        assert result.exit_code == 0
        assert "TOON" in result.output

    def test_analyze_cli_with_tokenizer(self) -> None:
        """Test --analyze with different tokenizer."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--analyze", "--tokenizer", "o200k_base"],
            input='{"key": "value"}',
        )

        assert result.exit_code == 0
        assert "o200k_base" in result.output

    def test_analyze_cli_no_color(self) -> None:
        """Test --analyze with --no-color."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["--analyze", "--no-color"], input='{"key": "value"}'
        )

        assert result.exit_code == 0
        # Output should work without errors
        assert "Token Analysis" in result.output

    def test_help_shows_analyze_options(self) -> None:
        """Test --help shows analyze options."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "--analyze" in result.output
        assert "--json" in result.output
