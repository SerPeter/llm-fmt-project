"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_json_data() -> dict:
    """Sample JSON data for testing."""
    return {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        ]
    }


@pytest.fixture
def sample_uniform_array() -> list[dict]:
    """Sample uniform array for TOON testing."""
    return [
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob", "active": False},
        {"id": 3, "name": "Charlie", "active": True},
    ]
