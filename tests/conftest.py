"""Pytest configuration and fixtures."""

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_json_data() -> dict[str, Any]:
    """Sample JSON data for testing."""
    return {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        ]
    }


@pytest.fixture
def sample_uniform_array() -> list[dict[str, Any]]:
    """Sample uniform array for TOON testing."""
    return [
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob", "active": False},
        {"id": 3, "name": "Charlie", "active": True},
    ]


@pytest.fixture
def simple_object() -> dict[str, Any]:
    """Simple key-value object."""
    return {"name": "test", "value": 42}


@pytest.fixture
def uniform_array() -> list[dict[str, Any]]:
    """Uniform array of user objects."""
    return [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
        {"id": 3, "name": "Carol", "email": "carol@example.com"},
    ]


@pytest.fixture
def nested_config() -> dict[str, Any]:
    """Deeply nested configuration object."""
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "credentials": {"user": "admin", "password": "secret"},
        },
        "features": ["auth", "logging"],
    }


@pytest.fixture
def large_array() -> list[dict[str, Any]]:
    """Large array with 1000 items for performance testing."""
    return [{"id": i, "value": f"item_{i}"} for i in range(1000)]


@pytest.fixture
def edge_case_data() -> dict[str, Any]:
    """Data with edge cases: nulls, booleans, special chars."""
    return {
        "null_value": None,
        "true_value": True,
        "false_value": False,
        "empty_string": "",
        "empty_array": [],
        "empty_object": {},
        "special_chars": "Hello, World! \"quotes\" and 'apostrophes'",
        "unicode": "日本語 émoji 🎉",
        "numbers": {
            "integer": 42,
            "negative": -100,
            "float": 3.14159,
            "zero": 0,
        },
    }


@pytest.fixture
def fixture_file(tmp_path: Path):
    """Factory for creating temp JSON files."""

    def _create(data: Any, name: str = "test.json") -> Path:
        path = tmp_path / name
        path.write_text(json.dumps(data))
        return path

    return _create


@pytest.fixture
def yaml_fixture_file(tmp_path: Path):
    """Factory for creating temp YAML files."""
    import yaml

    def _create(data: Any, name: str = "test.yaml") -> Path:
        path = tmp_path / name
        path.write_text(yaml.safe_dump(data))
        return path

    return _create
