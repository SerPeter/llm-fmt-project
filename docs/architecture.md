# Architecture

llm-fmt uses a Rust core with Python bindings via PyO3. The core implements a composable pipeline architecture following Unix philosophy: each stage does one thing well, and stages can be combined to build complex transformations.

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Python Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────────┐  │
│  │  cli.py  │  │ config.py│  │ __init__.py (API exports)    │  │
│  └────┬─────┘  └────┬─────┘  └──────────────┬───────────────┘  │
│       │             │                        │                  │
│       └─────────────┴────────────────────────┘                  │
│                              │                                  │
│                         PyO3 FFI                                │
└──────────────────────────────┼──────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                         Rust Core                               │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                   │
│  │ Parsers │ ──▶ │ Filters │ ──▶ │Encoders │                   │
│  └─────────┘     └─────────┘     └─────────┘                   │
│      │               │               │                          │
│      ▼               ▼               ▼                          │
│   bytes           Value           String                        │
│                (internal AST)                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
llm-fmt/
├── crates/
│   ├── llm-fmt-core/           # Rust library
│   │   ├── src/
│   │   │   ├── lib.rs          # Public API, Value type
│   │   │   ├── parsers/        # Input format parsers
│   │   │   │   ├── mod.rs
│   │   │   │   ├── json.rs
│   │   │   │   ├── yaml.rs
│   │   │   │   ├── xml.rs
│   │   │   │   └── csv.rs
│   │   │   ├── encoders/       # Output format encoders
│   │   │   │   ├── mod.rs
│   │   │   │   ├── toon.rs
│   │   │   │   ├── json.rs
│   │   │   │   ├── yaml.rs
│   │   │   │   ├── tsv.rs
│   │   │   │   └── csv.rs
│   │   │   ├── filters/        # Data transformations
│   │   │   │   ├── mod.rs
│   │   │   │   ├── include.rs  # Path filtering
│   │   │   │   ├── depth.rs    # Max depth limiting
│   │   │   │   └── truncate.rs # Array/string truncation
│   │   │   ├── pipeline.rs     # Pipeline orchestration
│   │   │   ├── analysis.rs     # Data shape detection, recommendations
│   │   │   ├── tokens.rs       # Token estimation
│   │   │   ├── benchdata.rs    # Benchmark data generators
│   │   │   └── bin/
│   │   │       ├── benchgen.rs
│   │   │       └── benchreport.rs
│   │   └── benches/            # Criterion benchmarks
│   │       ├── encoding.rs
│   │       ├── parsing.rs
│   │       └── pipeline.rs
│   │
│   └── llm-fmt-py/             # PyO3 bindings
│       └── src/
│           └── lib.rs          # Python module definition
│
├── src/llm_fmt/                # Python package
│   ├── __init__.py             # Public API exports
│   ├── cli.py                  # Click CLI
│   └── config.py               # Configuration system
│
└── tests/                      # Python tests
    ├── test_rust_bindings.py
    └── test_config.py
```

## Rust Core (`llm-fmt-core`)

### Value Type

The internal representation for all data:

```rust
pub enum Value {
    Null,
    Bool(bool),
    Number(Number),
    String(String),
    Array(Vec<Value>),
    Object(IndexMap<String, Value>),
}

pub enum Number {
    Integer(i64),
    Float(f64),
}
```

### Parser Trait

```rust
pub trait Parser: Send + Sync {
    fn parse(&self, input: &[u8]) -> Result<Value, ParseError>;
    fn format_name(&self) -> &'static str;
}
```

**Implementations:**
- `JsonParser` - via `serde_json`
- `YamlParser` - via `serde_yaml`
- `XmlParser` - via `quick-xml`
- `CsvParser` - via `csv` crate

### Encoder Trait

```rust
pub trait Encoder: Send + Sync {
    fn encode(&self, value: &Value) -> Result<String, EncodeError>;
    fn format_name(&self) -> &'static str;
}
```

**Implementations:**
- `ToonEncoder` - Tabular Object Notation
- `JsonEncoder` - Compact or pretty JSON
- `YamlEncoder` - YAML output
- `TsvEncoder` - Tab-separated values
- `CsvEncoder` - Comma-separated values

### Filter Trait

```rust
pub trait Filter: Send + Sync {
    fn apply(&self, value: Value) -> Result<Value, FilterError>;
}
```

**Implementations:**
- `IncludeFilter` - Keep only matching paths
- `MaxDepthFilter` - Limit nesting depth
- `TruncateFilter` - Limit array sizes and string lengths

### Pipeline

```rust
pub struct Pipeline {
    parser: Box<dyn Parser>,
    filters: Vec<Box<dyn Filter>>,
    encoder: Box<dyn Encoder>,
}

impl Pipeline {
    pub fn run(&self, input: &[u8]) -> Result<String, PipelineError> {
        let mut value = self.parser.parse(input)?;
        for filter in &self.filters {
            value = filter.apply(value)?;
        }
        self.encoder.encode(&value)
    }
}
```

### Analysis Module

```rust
pub enum DataShape {
    UniformArray,    // Array of objects with same keys
    SparseArray,     // Array of objects with varying keys
    FlatObject,      // Simple key-value object
    NestedObject,    // Object with nested structures
    TabularData,     // Array of arrays (rows)
    Mixed,           // Complex mixed structure
    Primitive,       // Single value
    Empty,           // Null or empty
}

pub fn detect_shape(value: &Value) -> DataShape;
pub fn select_format(value: &Value) -> &'static str;
pub fn analyze(value: &Value) -> AnalysisReport;
```

## PyO3 Bindings (`llm-fmt-py`)

The Python module exposes these functions:

```rust
#[pyfunction]
fn convert(
    py: Python,
    data: &[u8],
    format: &str,
    input_format: Option<&str>,
    max_depth: Option<usize>,
    // ... other options
) -> PyResult<String>;

#[pyfunction]
fn analyze(
    py: Python,
    data: &[u8],
    input_format: Option<&str>,
    output_json: Option<bool>,
) -> PyResult<PyObject>;

#[pyfunction]
fn detect_shape(data: &[u8], input_format: Option<&str>) -> PyResult<String>;

#[pyfunction]
fn select_format(data: &[u8], input_format: Option<&str>) -> PyResult<String>;
```

## Python Layer

### CLI (`cli.py`)

Uses Click for argument parsing. Loads configuration, then calls Rust functions:

```python
@click.command()
@click.option("--format", "-f", ...)
@click.option("--config", ...)
def main(...):
    config = load_config(config_path, no_config, cli_overrides)
    result = rust_convert(data, format=config.format, ...)
    click.echo(result)
```

### Configuration (`config.py`)

Hierarchical configuration system:

```
CLI args > Environment vars > Config files > pyproject.toml > Defaults
```

```python
@dataclass
class Config:
    format: str = "auto"
    input_format: str = "auto"
    limits: LimitsConfig
    truncation: TruncationConfig
    filter: FilterConfig
    output: OutputConfig
```

## Input Detection

### By Filename Extension

```rust
match extension {
    "json" => JsonParser,
    "yaml" | "yml" => YamlParser,
    "xml" => XmlParser,
    "csv" => CsvParser,
    "tsv" => TsvParser,
    _ => auto_detect(content),
}
```

### By Content (Magic Bytes)

```rust
fn auto_detect(data: &[u8]) -> Box<dyn Parser> {
    let trimmed = trim_whitespace(data);
    if starts_with(trimmed, b"{") || starts_with(trimmed, b"[") {
        JsonParser
    } else if starts_with(trimmed, b"<?xml") || starts_with(trimmed, b"<") {
        XmlParser
    } else if looks_like_csv(trimmed) {
        CsvParser
    } else {
        YamlParser  // YAML is superset of JSON, good fallback
    }
}
```

## Filter Chain

Filters are applied in the order specified on the CLI:

```bash
# Depth limit first, then truncation
llm-fmt data.json --max-depth 2 --max-items 100

# Order can affect output and performance
```

## Token Estimation

Uses a heuristic algorithm (~94% accuracy vs tiktoken):

```rust
pub fn estimate_tokens(text: &str) -> usize {
    // Approximation based on character patterns
    // Faster than loading a full tokenizer
}

pub fn calculate_savings(original: usize, converted: usize) -> f64 {
    ((original - converted) as f64 / original as f64) * 100.0
}
```

## Error Handling

Errors are typed and propagate through the pipeline:

```rust
#[derive(Debug, Error)]
pub enum PipelineError {
    #[error("Parse error: {0}")]
    Parse(#[from] ParseError),
    #[error("Filter error: {0}")]
    Filter(#[from] FilterError),
    #[error("Encode error: {0}")]
    Encode(#[from] EncodeError),
}
```

Python receives errors as exceptions with clear messages.

## Performance Characteristics

- **Parsing**: Single-pass, streaming where possible
- **Filtering**: In-place modification, no unnecessary copies
- **Encoding**: Direct string building, pre-allocated buffers
- **Memory**: Values are owned, no reference counting overhead

Typical throughput on 10K object arrays:
- JSON encoding: ~280 MiB/s
- TOON encoding: ~180 MiB/s
- YAML encoding: ~160 MiB/s

## Future Considerations

### Streaming Support

For very large files, add streaming parsers that yield values incrementally rather than loading everything into memory.

### Additional Formats

The trait-based architecture makes it easy to add new formats:
- TOML input
- MessagePack output
- Protocol Buffers

### WASM Target

The Rust core could be compiled to WebAssembly for browser usage.
