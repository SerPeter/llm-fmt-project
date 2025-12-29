"""Tests for data filters."""

import pytest

from llm_fmt.filters import IncludeFilter, MaxDepthFilter


class TestIncludeFilter:
    """Tests for JMESPath include filter."""

    def test_simple_key(self) -> None:
        """Test extracting a simple top-level key."""
        data = {"name": "Alice", "age": 30}
        result = IncludeFilter("name")(data)
        assert result == "Alice"

    def test_nested_path(self) -> None:
        """Test extracting nested path."""
        data = {"a": {"b": {"c": 1}}}
        result = IncludeFilter("a.b.c")(data)
        assert result == 1

    def test_array_index(self) -> None:
        """Test extracting array element by index."""
        data = {"items": [{"id": 1}, {"id": 2}, {"id": 3}]}
        result = IncludeFilter("items[0]")(data)
        assert result == {"id": 1}

    def test_array_wildcard(self) -> None:
        """Test extracting field from all array elements."""
        data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
        result = IncludeFilter("users[*].id")(data)
        assert result == [1, 2]

    def test_array_all_elements(self) -> None:
        """Test extracting all array elements."""
        data = {"items": [1, 2, 3]}
        result = IncludeFilter("items[*]")(data)
        assert result == [1, 2, 3]

    def test_filter_expression(self) -> None:
        """Test filtering by value condition."""
        data = {"items": [{"price": 5}, {"price": 15}, {"price": 25}]}
        result = IncludeFilter("items[?price > `10`]")(data)
        assert result == [{"price": 15}, {"price": 25}]

    def test_filter_equality(self) -> None:
        """Test filtering by equality."""
        data = {
            "users": [
                {"name": "Alice", "active": True},
                {"name": "Bob", "active": False},
                {"name": "Carol", "active": True},
            ]
        }
        result = IncludeFilter("users[?active].name")(data)
        assert result == ["Alice", "Carol"]

    def test_flatten_arrays(self) -> None:
        """Test flattening nested arrays."""
        data = {"groups": [{"items": [1, 2]}, {"items": [3, 4]}]}
        result = IncludeFilter("groups[].items[]")(data)
        assert result == [1, 2, 3, 4]

    def test_multiselect_hash(self) -> None:
        """Test multi-select hash projection."""
        data = {"user": {"firstName": "Alice", "lastName": "Smith", "age": 30}}
        result = IncludeFilter("user.{name: firstName, surname: lastName}")(data)
        assert result == {"name": "Alice", "surname": "Smith"}

    def test_no_match_returns_original(self) -> None:
        """Test that non-matching expression returns original data."""
        data = {"name": "Alice"}
        result = IncludeFilter("nonexistent")(data)
        assert result == {"name": "Alice"}

    def test_invalid_expression_raises(self) -> None:
        """Test that invalid expression raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JMESPath expression"):
            IncludeFilter("[invalid")

    def test_pipe_expression(self) -> None:
        """Test pipe expression to get first element."""
        data = {"items": [{"id": 1}, {"id": 2}]}
        result = IncludeFilter("items[*].id | [0]")(data)
        assert result == 1

    def test_list_input(self) -> None:
        """Test with list as root input."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = IncludeFilter("[*].id")(data)
        assert result == [1, 2, 3]

    def test_string_comparison(self) -> None:
        """Test filtering by string value."""
        data = {
            "items": [
                {"type": "book", "name": "Python"},
                {"type": "video", "name": "JS Course"},
                {"type": "book", "name": "Rust"},
            ]
        }
        result = IncludeFilter("items[?type == 'book'].name")(data)
        assert result == ["Python", "Rust"]

    def test_select_specific_fields(self) -> None:
        """Test selecting specific fields (alternative to exclude)."""
        data = {
            "users": [
                {"id": 1, "name": "Alice", "password": "secret"},
                {"id": 2, "name": "Bob", "password": "hidden"},
            ]
        }
        # Instead of excluding password, select only the fields you want
        result = IncludeFilter("users[*].{id: id, name: name}")(data)
        assert result == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


class TestMaxDepthFilter:
    """Tests for max depth filter."""

    def test_depth_zero(self) -> None:
        """Test depth 0 truncates nested structures."""
        data = {"a": {"b": 1}, "c": [1, 2]}
        result = MaxDepthFilter(0)(data)
        assert result == {"a": {"...": "1 keys"}, "c": ["... 2 items"]}

    def test_depth_one(self) -> None:
        """Test depth 1 keeps one level."""
        data = {"a": {"b": {"c": 1}}}
        result = MaxDepthFilter(1)(data)
        assert result == {"a": {"b": {"...": "1 keys"}}}

    def test_depth_preserves_primitives(self) -> None:
        """Test primitives are preserved at any depth."""
        data = {"name": "Alice", "age": 30}
        result = MaxDepthFilter(0)(data)
        assert result == {"name": "Alice", "age": 30}

    def test_negative_depth_raises(self) -> None:
        """Test negative depth raises ValueError."""
        with pytest.raises(ValueError, match="must be non-negative"):
            MaxDepthFilter(-1)

    def test_deep_enough_returns_unchanged(self) -> None:
        """Test data shallower than max depth is unchanged."""
        data = {"a": 1}
        result = MaxDepthFilter(5)(data)
        assert result == {"a": 1}

    def test_array_depth(self) -> None:
        """Test depth limiting within arrays."""
        data = {"items": [{"nested": {"deep": 1}}]}
        result = MaxDepthFilter(2)(data)
        assert result == {"items": [{"nested": {"...": "1 keys"}}]}

    def test_nested_arrays(self) -> None:
        """Test depth limiting with nested arrays."""
        data = {"matrix": [[{"value": 1}, {"value": 2}], [{"value": 3}]]}
        result = MaxDepthFilter(2)(data)
        assert result == {
            "matrix": [[{"...": "1 keys"}, {"...": "1 keys"}], [{"...": "1 keys"}]]
        }

    def test_root_array(self) -> None:
        """Test depth limiting when root is an array."""
        data = [{"a": {"b": 1}}, {"a": {"c": 2}}]
        result = MaxDepthFilter(1)(data)
        assert result == [{"a": {"...": "1 keys"}}, {"a": {"...": "1 keys"}}]


class TestFilterChaining:
    """Tests for chaining multiple filters."""

    def test_filter_then_depth(self) -> None:
        """Test chaining filter and depth limit."""
        data = {"deep": {"a": {"b": {"c": {"d": 1}}}}}

        result = IncludeFilter("deep")(data)
        result = MaxDepthFilter(1)(result)

        assert result == {"a": {"b": {"...": "1 keys"}}}

    def test_multiple_include_filters(self) -> None:
        """Test chaining multiple include filters."""
        data = {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False},
            ]
        }

        # First filter active users, then extract names
        result = IncludeFilter("users[?active]")(data)
        result = IncludeFilter("[*].name")(result)

        assert result == ["Alice"]
