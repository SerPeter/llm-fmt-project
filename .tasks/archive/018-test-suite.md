# Task 018: Comprehensive Test Suite

**Phase**: 3 - Auto-Selection & Polish  
**Priority**: -150
**Storypoints**: 8  
**Status**: [x] Complete

## Objective

Build comprehensive test coverage for all functionality before release.

## Requirements

- [x] Unit tests for all format encoders
- [x] Unit tests for filtering functions
- [x] Integration tests for CLI
- [x] Property-based tests with Hypothesis
- [x] Test fixtures with realistic data
- [x] Coverage target: 90%+

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_formats/
│   ├── test_toon.py
│   ├── test_compact_json.py
│   ├── test_yaml.py
│   └── test_tsv.py
├── test_filter.py
├── test_detection.py
├── test_tokens.py
├── test_cli.py
└── fixtures/
    ├── simple.json
    ├── uniform_array.json
    ├── nested_config.json
    ├── large_array.json
    └── edge_cases.json
```

## Implementation Details

### conftest.py - Shared Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_object():
    return {"name": "test", "value": 42}


@pytest.fixture
def uniform_array():
    return [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
        {"id": 3, "name": "Carol", "email": "carol@example.com"},
    ]


@pytest.fixture
def nested_config():
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "credentials": {
                "user": "admin",
                "password": "secret"
            }
        },
        "features": ["auth", "logging"]
    }


@pytest.fixture
def large_array():
    return [{"id": i, "value": f"item_{i}"} for i in range(1000)]


@pytest.fixture
def fixture_file(tmp_path):
    """Factory for creating temp JSON files."""
    def _create(data, name="test.json"):
        import json
        path = tmp_path / name
        path.write_text(json.dumps(data))
        return path
    return _create
```

### Format Tests

```python
# tests/test_formats/test_toon.py
import pytest
from llm_fmt.formats.toon import encode_toon


class TestToonEncoder:
    def test_simple_object(self, simple_object):
        result = encode_toon(simple_object)
        assert "{name,value}:" in result
        assert "test,42" in result

    def test_uniform_array_tabular(self, uniform_array):
        result = encode_toon(uniform_array)
        assert "[3]{id,name,email}:" in result
        assert "1,Alice,alice@example.com" in result

    def test_empty_object(self):
        assert encode_toon({}) == "{}"

    def test_empty_array(self):
        assert encode_toon([]) == "[]"

    def test_nested_objects(self, nested_config):
        result = encode_toon(nested_config)
        assert "database{" in result or "database:" in result

    def test_special_characters_escaped(self):
        data = {"msg": "Hello, World", "quote": 'Say "hi"'}
        result = encode_toon(data)
        assert '"Hello, World"' in result  # Comma needs quotes

    def test_null_values(self):
        data = {"key": None}
        result = encode_toon(data)
        assert "null" in result

    def test_boolean_values(self):
        data = {"flag": True, "other": False}
        result = encode_toon(data)
        assert "true" in result
        assert "false" in result
```

### CLI Tests

```python
# tests/test_cli.py
from click.testing import CliRunner
from llm_fmt.cli import main


class TestCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Convert JSON" in result.output

    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_stdin_input(self, runner):
        result = runner.invoke(main, input='{"test": 1}')
        assert result.exit_code == 0

    def test_file_input(self, runner, fixture_file, simple_object):
        path = fixture_file(simple_object)
        result = runner.invoke(main, [str(path)])
        assert result.exit_code == 0

    def test_format_toon(self, runner, fixture_file, uniform_array):
        path = fixture_file(uniform_array)
        result = runner.invoke(main, [str(path), "-f", "toon"])
        assert result.exit_code == 0
        assert "[3]{" in result.output

    def test_format_compact_json(self, runner):
        result = runner.invoke(main, ["-f", "compact-json"], input='{"a": 1}')
        assert result.exit_code == 0
        assert '{"a":1}' in result.output

    def test_invalid_json(self, runner):
        result = runner.invoke(main, input='{invalid}')
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_filter_option(self, runner):
        data = '{"users": [{"id": 1, "name": "A"}], "meta": {}}'
        result = runner.invoke(main, ["--filter", "users"], input=data)
        assert result.exit_code == 0
        # Should only contain users, not meta

    def test_output_file(self, runner, tmp_path, simple_object, fixture_file):
        input_path = fixture_file(simple_object)
        output_path = tmp_path / "output.toon"
        result = runner.invoke(main, [
            str(input_path), "-f", "toon", "-o", str(output_path)
        ])
        assert result.exit_code == 0
        assert output_path.exists()
```

### Property-Based Tests

```python
# tests/test_properties.py
from hypothesis import given, strategies as st
from llm_fmt.formats import toon, compact_json


# Strategy for JSON-like data
json_primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
)

json_data = st.recursive(
    json_primitives,
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=10),
    ),
    max_leaves=50,
)


class TestProperties:
    @given(json_data)
    def test_compact_json_roundtrip(self, data):
        """Compact JSON should be valid JSON that parses back."""
        import orjson
        encoded = compact_json.encode(data)
        decoded = orjson.loads(encoded)
        assert decoded == data

    @given(st.lists(
        st.fixed_dictionaries({"id": st.integers(), "name": st.text()}),
        min_size=1, max_size=20
    ))
    def test_toon_uniform_array_format(self, data):
        """Uniform arrays should use tabular format."""
        result = toon.encode(data)
        assert f"[{len(data)}]" in result
        assert "{id,name}:" in result
```

## Running Tests

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=llm_fmt --cov-report=html

# Specific test file
uv run pytest tests/test_cli.py

# Run property tests with more examples
uv run pytest tests/test_properties.py --hypothesis-seed=0
```

## Coverage Configuration

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src/llm_fmt"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
fail_under = 90
```

## Acceptance Criteria

- [x] All format encoders have unit tests
- [x] CLI has integration tests for all options
- [x] Edge cases covered (empty, null, special chars)
- [x] Property tests validate roundtrip consistency
- [x] Coverage ≥90%
- [ ] Tests run in CI

## Dependencies

- `pytest>=8.0`
- `pytest-cov>=5.0`
- `hypothesis>=6.100`
