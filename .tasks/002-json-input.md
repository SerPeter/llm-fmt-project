# Task 002: JSON Input Parsing

**Phase**: 1 - MVP  
**Priority**: +200
**Storypoints**: 3  
**Status**: [ ] Not started

## Objective

Implement fast, robust JSON input parsing using orjson.

## Requirements

- [ ] Parse JSON from file path argument
- [ ] Parse JSON from stdin (pipe support)
- [ ] Handle large files efficiently (streaming consideration)
- [ ] Provide clear error messages for invalid JSON
- [ ] Support both objects and arrays as root elements

## Implementation Details

### Core Parser Module

```python
# src/llm_fmt/parsers/json_parser.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import orjson


class ParseError(Exception):
    """Raised when input cannot be parsed."""
    pass


def parse_json(source: str | Path | None = None) -> Any:
    """
    Parse JSON from file or stdin.
    
    Args:
        source: File path, "-" for stdin, or None for stdin
        
    Returns:
        Parsed JSON data (dict, list, or primitive)
        
    Raises:
        ParseError: If JSON is invalid or file not found
    """
    try:
        if source is None or source == "-":
            content = sys.stdin.buffer.read()
        else:
            path = Path(source)
            if not path.exists():
                raise ParseError(f"File not found: {source}")
            content = path.read_bytes()
        
        return orjson.loads(content)
    
    except orjson.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON: {e}") from e
    except OSError as e:
        raise ParseError(f"Cannot read input: {e}") from e


def detect_input_format(source: str | Path) -> str:
    """
    Detect input format from file extension.
    
    Returns: "json", "yaml", "xml", or "unknown"
    """
    if source == "-":
        return "json"  # Default for stdin
    
    path = Path(source)
    suffix = path.suffix.lower()
    
    return {
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".xml": "xml",
    }.get(suffix, "unknown")
```

### Error Handling

```python
# Detailed error messages with line/column info
try:
    data = parse_json("input.json")
except ParseError as e:
    click.echo(f"Error: {e}", err=True)
    sys.exit(1)
```

### orjson Performance Notes

orjson is 10-20x faster than stdlib json:
- Written in Rust
- Returns `bytes`, decode with `.decode()` if string needed
- `orjson.loads()` accepts both `str` and `bytes`
- `orjson.dumps()` returns `bytes`, use `OPT_INDENT_2` for pretty

## Acceptance Criteria

- [ ] `llm-fmt input.json` parses file correctly
- [ ] `cat input.json | llm-fmt` parses stdin
- [ ] `llm-fmt - < input.json` also works
- [ ] Invalid JSON shows clear error message with position
- [ ] Non-existent file shows "File not found" error
- [ ] Large files (100MB+) don't crash (memory permitting)

## Test Cases

```python
def test_parse_valid_json(tmp_path):
    f = tmp_path / "test.json"
    f.write_text('{"key": "value"}')
    assert parse_json(f) == {"key": "value"}

def test_parse_array():
    ...

def test_parse_invalid_json():
    with pytest.raises(ParseError, match="Invalid JSON"):
        parse_json(...)

def test_parse_stdin(monkeypatch):
    ...
```

## Dependencies

- `orjson>=3.10`

## Notes

- orjson doesn't support JSON5 or trailing commas
- Consider adding `--lenient` flag later for relaxed parsing
- Binary read mode (`rb`) is important for orjson performance
