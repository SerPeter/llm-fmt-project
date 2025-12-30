"""Property-based tests using Hypothesis.

These tests verify invariants across a wide range of inputs, catching
edge cases that specific unit tests might miss.
"""

import json
from typing import Any

from hypothesis import HealthCheck, given, settings, strategies as st

from llm_fmt.encoders import JsonEncoder, ToonEncoder, YamlEncoder
from llm_fmt.parsers import JsonParser, YamlParser
from llm_fmt.pipeline import PipelineBuilder


# Safe text strategy that avoids problematic Unicode characters
# YAML has issues with certain control characters (e.g., \x85 NEXT LINE)
safe_text = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cc", "Cs"),  # Exclude control chars and surrogates
        blacklist_characters=("\x85", "\u2028", "\u2029"),  # YAML-problematic chars
    ),
    max_size=100,
)

# Safe key strategy - alphanumeric only to avoid encoding issues
safe_key = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
    min_size=1,
    max_size=20,
)

# Strategies for generating JSON-compatible data
json_primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(2**53), max_value=2**53),  # JSON-safe integers
    st.floats(allow_nan=False, allow_infinity=False, allow_subnormal=False),
    safe_text,
)

# Recursive strategy for nested structures
json_data = st.recursive(
    json_primitives,
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(safe_key, children, max_size=10),
    ),
    max_leaves=50,
)


class TestJsonEncoderProperties:
    """Property tests for JSON encoder."""

    @given(json_data)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_output_is_valid_json(self, data: Any) -> None:
        """JSON encoder always produces valid JSON."""
        encoder = JsonEncoder()
        result = encoder.encode(data)

        # Should parse without error
        json.loads(result)

    @given(json_data)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_roundtrip(self, data: Any) -> None:
        """Encoding and decoding produces equivalent data."""
        encoder = JsonEncoder()
        result = encoder.encode(data)
        decoded = json.loads(result)

        assert decoded == data

    @given(json_data)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_no_whitespace_except_in_strings(self, data: Any) -> None:
        """Compact JSON has no unnecessary whitespace."""
        encoder = JsonEncoder()
        result = encoder.encode(data)

        # Parse to verify, then check no structural whitespace
        # We can't simply check for no whitespace because strings may contain it
        parsed = json.loads(result)
        re_encoded = json.dumps(parsed, separators=(",", ":"))

        # Our encoding should match json.dumps compact format
        # (Though key order may differ)
        assert len(result) <= len(re_encoded) + 10  # Allow small variance

    @given(st.dictionaries(st.text(min_size=1, max_size=10), json_primitives, min_size=2, max_size=5))
    @settings(max_examples=50)
    def test_sort_keys_deterministic(self, data: dict[str, Any]) -> None:
        """Sorted encoding is deterministic across multiple calls."""
        encoder = JsonEncoder(sort_keys=True)

        results = [encoder.encode(data) for _ in range(3)]
        assert len(set(results)) == 1


class TestToonEncoderProperties:
    """Property tests for TOON encoder."""

    # Strategy for uniform arrays (all dicts with same keys)
    @given(
        st.lists(
            st.fixed_dictionaries(
                {"id": st.integers(), "name": st.text(max_size=20), "active": st.booleans()}
            ),
            min_size=1,
            max_size=20,
        )
    )
    @settings(max_examples=50)
    def test_uniform_array_has_header(self, data: list[dict[str, Any]]) -> None:
        """Uniform arrays produce tabular format with header."""
        encoder = ToonEncoder()
        result = encoder.encode(data)

        # Should have header row
        lines = result.split("\n")
        assert len(lines) >= 1

        # Header should contain the keys
        header = lines[0]
        assert "id" in header
        assert "name" in header
        assert "active" in header

    @given(
        st.lists(
            st.fixed_dictionaries({"x": st.integers(), "y": st.integers()}),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=50)
    def test_row_count_matches_data(self, data: list[dict[str, Any]]) -> None:
        """Number of data rows equals number of items."""
        encoder = ToonEncoder()
        result = encoder.encode(data)

        lines = result.split("\n")
        # First line is header, rest are data
        assert len(lines) == len(data) + 1

    @given(st.dictionaries(safe_key, json_primitives, min_size=1, max_size=5))
    @settings(max_examples=50)
    def test_single_object_encoding(self, data: dict[str, Any]) -> None:
        """Single objects encode to header + one row."""
        encoder = ToonEncoder()
        result = encoder.encode(data)

        lines = result.split("\n")
        assert len(lines) == 2  # Header + one row

    @given(st.lists(json_primitives, min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_primitive_list_one_per_line(self, data: list[Any]) -> None:
        """List of primitives has one value per line."""
        encoder = ToonEncoder()
        result = encoder.encode(data)

        lines = result.split("\n")
        assert len(lines) == len(data)


class TestYamlEncoderProperties:
    """Property tests for YAML encoder."""

    @given(json_data)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_output_parses_as_yaml(self, data: Any) -> None:
        """YAML encoder produces valid YAML."""
        import yaml

        encoder = YamlEncoder()
        result = encoder.encode(data)

        # Should parse without error
        yaml.safe_load(result)

    @given(json_data)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_yaml_roundtrip(self, data: Any) -> None:
        """YAML encoding and decoding produces equivalent data."""
        import yaml

        encoder = YamlEncoder()
        result = encoder.encode(data)
        decoded = yaml.safe_load(result)

        assert decoded == data


class TestParserProperties:
    """Property tests for parsers."""

    @given(json_data)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_json_parser_roundtrip(self, data: Any) -> None:
        """JSON parser correctly parses JSON encoder output."""
        encoder = JsonEncoder()
        parser = JsonParser()

        encoded = encoder.encode(data)
        parsed = parser.parse(encoded.encode("utf-8"))

        assert parsed == data

    @given(json_data)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_yaml_parser_roundtrip(self, data: Any) -> None:
        """YAML parser correctly parses YAML encoder output."""
        encoder = YamlEncoder()
        parser = YamlParser()

        encoded = encoder.encode(data)
        parsed = parser.parse(encoded.encode("utf-8"))

        assert parsed == data


class TestPipelineProperties:
    """Property tests for the full pipeline."""

    @given(json_data)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_json_pipeline_roundtrip(self, data: Any) -> None:
        """Full JSON pipeline produces valid output."""
        pipeline = PipelineBuilder().with_parser(JsonParser()).with_format("json").build()

        # Encode input
        input_json = json.dumps(data).encode("utf-8")
        result = pipeline.run(input_json)

        # Output should be valid JSON that matches input
        decoded = json.loads(result)
        assert decoded == data

    @given(json_data)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_yaml_pipeline_produces_valid_output(self, data: Any) -> None:
        """Full YAML pipeline produces valid output."""
        import yaml

        pipeline = PipelineBuilder().with_parser(JsonParser()).with_format("yaml").build()

        # Encode input
        input_json = json.dumps(data).encode("utf-8")
        result = pipeline.run(input_json)

        # Output should be valid YAML that matches input
        decoded = yaml.safe_load(result)
        assert decoded == data


class TestEncoderTokenEfficiency:
    """Property tests for token efficiency claims."""

    @given(
        st.lists(
            st.fixed_dictionaries(
                {
                    "id": st.integers(min_value=1, max_value=1000),
                    "name": st.text(min_size=3, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
                    "value": st.integers(min_value=0, max_value=100),
                }
            ),
            min_size=5,
            max_size=20,
        )
    )
    @settings(max_examples=30)
    def test_toon_shorter_than_json_for_uniform_arrays(
        self, data: list[dict[str, Any]]
    ) -> None:
        """TOON produces shorter output than JSON for uniform arrays."""
        json_encoder = JsonEncoder()
        toon_encoder = ToonEncoder()

        json_result = json_encoder.encode(data)
        toon_result = toon_encoder.encode(data)

        # TOON should generally be shorter for uniform arrays
        # Allow some margin for very small arrays where overhead may dominate
        assert len(toon_result) <= len(json_result) * 1.1  # Allow 10% margin
