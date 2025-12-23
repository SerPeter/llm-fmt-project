# Architecture

llm-fmt uses a composable pipeline architecture following Unix philosophy: each stage does one thing well, and stages can be combined to build complex transformations.

## Pipeline Overview

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Input  │ ──▶ │ Filter  │ ──▶ │ Output  │
│ (parse) │     │(transform)    │(encode) │
└─────────┘     └─────────┘     └─────────┘
   bytes          Any             str
     ▼             ▼               ▼
  Python obj    Python obj     formatted text
```

**Stages:**

1. **Input (Parser)**: Detects format and parses bytes into Python objects
2. **Filter (Transform)**: Applies transformations (include/exclude paths, depth limiting)
3. **Output (Encoder)**: Encodes Python objects to the target format

## Module Structure

```
src/llm_fmt/
├── __init__.py
├── cli.py              # Click CLI, arg parsing, orchestration
├── pipeline.py         # Pipeline runner, connects stages
├── parsers/
│   ├── __init__.py     # detect_parser(), Parser protocol
│   ├── json_parser.py
│   ├── yaml_parser.py
│   └── xml_parser.py
├── filters/
│   ├── __init__.py     # Filter protocol, chain builder
│   ├── include.py      # --filter (dpath include)
│   ├── exclude.py      # --exclude (dpath exclude)
│   └── depth.py        # --max-depth
├── encoders/
│   ├── __init__.py     # Encoder protocol
│   ├── toon.py
│   ├── json_encoder.py
│   └── yaml_encoder.py
└── errors.py           # Error collection/reporting
```

## Input Detection

### By Filename Extension

```python
EXTENSION_MAP = {
    ".json": JsonParser,
    ".yaml": YamlParser,
    ".yml": YamlParser,
    ".xml": XmlParser,
}
```

### By Magic Bytes (stdin)

When input is piped, detect format from content:

```python
def detect_format(data: bytes) -> Parser:
    stripped = data.lstrip()
    if stripped.startswith((b"{", b"[")):
        return JsonParser()
    if stripped.startswith(b"<?xml") or stripped.startswith(b"<"):
        return XmlParser()
    # Default to YAML (superset of JSON, handles most text)
    return YamlParser()
```

## Filter Chain

Filters are composable and applied in CLI argument order. This gives users explicit control over execution order, which can affect performance depending on the data shape.

**Example:**
```bash
# Depth limit first, then path filter
llm-fmt data.json --max-depth 2 --filter "users/*"

# Path filter first, then depth limit
llm-fmt data.json --filter "users/*" --max-depth 2
```

**Performance considerations:**
- **Deep but narrow data**: `--max-depth` first cuts the tree early
- **Wide but shallow data**: `--filter` first narrows the dataset

### Filter Protocol

```python
class Filter(Protocol):
    def apply(self, data: Any) -> Any:
        """Transform data."""
        ...

    def apply_stream(self, data: Iterator[Any]) -> Iterator[Any]:
        """Streaming transform (future)."""
        ...

class FilterChain:
    def __init__(self, filters: list[Filter]):
        self.filters = filters

    def apply(self, data: Any) -> Any:
        for f in self.filters:
            data = f.apply(data)
        return data
```

### Available Filters

| Filter | CLI Flag | Description |
|--------|----------|-------------|
| Include | `--filter` | Keep only paths matching dpath pattern |
| Exclude | `--exclude` | Remove paths matching dpath pattern |
| MaxDepth | `--max-depth` | Truncate data beyond specified depth |

## Output Encoding

Default output format is TOON (Tabular Object Notation), which provides 30-60% token savings for uniform arrays.

### Encoder Protocol

```python
class Encoder(Protocol):
    def encode(self, data: Any) -> str:
        """Encode to output format."""
        ...

    def encode_stream(self, data: Iterator[Any]) -> Iterator[str]:
        """Streaming encode (future)."""
        ...
```

### Available Encoders

| Format | Token Savings | Best For |
|--------|---------------|----------|
| TOON | 30-60% | Uniform arrays of objects |
| TSV | 40-50% | Flat tabular data |
| YAML | 20-40% | Human-readable, nested data |
| Compact JSON | 10-20% | Compatibility, any structure |

## Core Protocols (Streaming-Ready)

All protocols include both batch and streaming interfaces. The streaming interface is prepared for future implementation.

### Parser Protocol

```python
from typing import Protocol, Iterator, Any
from pathlib import Path

class Parser(Protocol):
    def parse(self, data: bytes) -> Any:
        """Parse bytes into Python object."""
        ...

    def parse_stream(self, stream: Iterator[bytes]) -> Iterator[Any]:
        """Streaming parse (future)."""
        ...

def detect_parser(filename: Path | None, data: bytes | None) -> Parser:
    """Auto-detect parser from extension or magic bytes."""
    ...
```

## Pipeline Runner

```python
from dataclasses import dataclass
from typing import Any, Iterator

@dataclass
class Pipeline:
    parser: Parser
    filters: FilterChain
    encoder: Encoder

    def run(self, input_data: bytes) -> str:
        data = self.parser.parse(input_data)
        data = self.filters.apply(data)
        return self.encoder.encode(data)

    # Future: streaming version
    def run_stream(self, input_stream: Iterator[bytes]) -> Iterator[str]:
        data = self.parser.parse_stream(input_stream)
        data = self.filters.apply_stream(data)
        return self.encoder.encode_stream(data)
```

## Error Handling

Strategy: **Validate upfront, fail fast on runtime errors.**

All configuration (CLI arguments, filter patterns) is validated before the pipeline runs. This catches multiple errors at once, avoiding repeated command invocations.

```python
from dataclasses import dataclass

@dataclass
class ValidationError:
    location: str  # e.g., "--filter[0]"
    message: str

class ConfigurationError(Exception):
    """Raised when CLI args are invalid."""
    def __init__(self, errors: list[ValidationError]):
        self.errors = errors

    def __str__(self) -> str:
        return "\n".join(f"{e.location}: {e.message}" for e in self.errors)
```

**Validation example:**
```python
def validate_filters(filters: list[str]) -> list[ValidationError]:
    errors = []
    for i, pattern in enumerate(filters):
        if not is_valid_dpath(pattern):
            errors.append(ValidationError(f"--filter[{i}]", f"Invalid path: {pattern}"))
    return errors
```

## CLI Usage Examples

```bash
# Basic conversion (auto-detect input, output as TOON)
llm-fmt data.json

# With filters (applied in order specified)
llm-fmt data.json --filter "users/*" --exclude "*/password" --max-depth 3

# Explicit format override
llm-fmt data.json --input-format json --output-format yaml

# Stdin with format hint
cat data.json | llm-fmt --input-format json

# Stdin with auto-detection (magic bytes)
cat data.json | llm-fmt
```

## Future Considerations

### Query Plan Optimization

Currently filters are applied in CLI argument order. A future optimization could analyze the filter chain and data characteristics to determine optimal execution order, similar to database query planners.

### Streaming Support

All protocols include `*_stream` methods for future streaming implementation. This will enable processing of large files without loading entirely into memory.

### Additional Input Formats

The parser architecture supports adding new input formats (CSV, TOML, etc.) by implementing the `Parser` protocol.
