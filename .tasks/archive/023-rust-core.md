# Task 023: Rust Core with PyO3 Bindings

**Phase**: 4 - Performance & Extensions
**Priority**: +80
**Storypoints**: 21
**Status**: [~] In progress

## Objective

Rewrite the core logic in Rust and expose it to Python via PyO3. The Python package becomes a thin wrapper around the Rust implementation, maintaining full API compatibility.

## Architecture

```
llm-fmt/
├── crates/
│   ├── llm-fmt-core/           # Pure Rust library
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── parsers/
│   │       │   ├── mod.rs
│   │       │   ├── json.rs
│   │       │   ├── yaml.rs
│   │       │   ├── xml.rs
│   │       │   └── csv.rs
│   │       ├── encoders/
│   │       │   ├── mod.rs
│   │       │   ├── toon.rs
│   │       │   ├── json.rs
│   │       │   ├── yaml.rs
│   │       │   └── tsv.rs
│   │       ├── filters/
│   │       │   ├── mod.rs
│   │       │   ├── depth.rs
│   │       │   ├── jmespath.rs
│   │       │   └── truncate.rs
│   │       ├── pipeline.rs
│   │       ├── tokens.rs
│   │       ├── analyze.rs
│   │       └── error.rs
│   │
│   └── llm-fmt-py/             # PyO3 bindings
│       ├── Cargo.toml
│       └── src/
│           └── lib.rs
│
├── python/
│   └── llm_fmt/
│       ├── __init__.py         # Re-exports from Rust
│       ├── _native.pyi         # Type stubs
│       ├── cli.py              # Click CLI (thin wrapper)
│       └── _fallback/          # Pure Python fallback (optional)
│
├── Cargo.toml                  # Workspace
├── pyproject.toml              # maturin config
└── tests/
    ├── rust/                   # Rust unit tests
    └── python/                 # Python integration tests
```

## Implementation Phases

### Phase 1: Rust Core Foundation
**Estimated: 5 story points**

Set up Rust workspace and implement core data types.

- [x] Initialize Cargo workspace with two crates
- [x] Define `Value` enum (mirrors serde_json::Value but owned)
- [x] Define error types with `thiserror`
- [ ] Set up basic CI for Rust (cargo test, clippy, fmt)

```rust
// crates/llm-fmt-core/src/lib.rs
pub mod parsers;
pub mod encoders;
pub mod filters;
pub mod pipeline;
pub mod error;

pub use error::{Error, Result};

/// Core value type for all operations
#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    Null,
    Bool(bool),
    Number(Number),
    String(String),
    Array(Vec<Value>),
    Object(IndexMap<String, Value>),  // Preserve insertion order
}
```

### Phase 2: Parsers
**Estimated: 3 story points**

Implement input parsers using established crates.

- [x] JSON parser (`serde_json`)
- [x] YAML parser (`serde_yaml`)
- [x] XML parser (`quick-xml`)
- [x] CSV parser (`csv` crate)
- [x] Auto-detection from content/extension

```rust
// crates/llm-fmt-core/src/parsers/mod.rs
pub trait Parser: Send + Sync {
    fn parse(&self, input: &[u8]) -> Result<Value>;
}

pub fn detect_parser(filename: Option<&str>, content: &[u8]) -> Box<dyn Parser>;
```

**Crate dependencies:**
```toml
[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
serde_yaml = "0.9"
quick-xml = { version = "0.31", features = ["serialize"] }
csv = "1"
indexmap = { version = "2", features = ["serde"] }
```

### Phase 3: Encoders
**Estimated: 4 story points**

Implement output encoders with focus on performance.

- [x] TOON encoder (primary optimization target)
- [x] Compact JSON encoder
- [x] YAML encoder
- [x] TSV encoder
- [x] CSV encoder

```rust
// crates/llm-fmt-core/src/encoders/mod.rs
pub trait Encoder: Send + Sync {
    fn encode(&self, value: &Value) -> Result<String>;
}

// TOON with pre-allocated buffer for performance
pub struct ToonEncoder {
    buffer: String,
}

impl ToonEncoder {
    pub fn encode_to(&mut self, value: &Value) -> Result<&str> {
        self.buffer.clear();
        self.write_value(value)?;
        Ok(&self.buffer)
    }
}
```

### Phase 4: Filters
**Estimated: 4 story points**

Implement filtering with JMESPath support.

- [x] MaxDepth filter (straightforward port)
- [x] Include filter (path-based extraction with wildcards)
- [ ] Truncation filters (from Task 022)
- [x] Filter chain composition

```rust
// crates/llm-fmt-core/src/filters/mod.rs
pub trait Filter: Send + Sync {
    fn apply(&self, value: Value) -> Result<Value>;
}

pub struct FilterChain {
    filters: Vec<Box<dyn Filter>>,
}

impl Filter for FilterChain {
    fn apply(&self, mut value: Value) -> Result<Value> {
        for filter in &self.filters {
            value = filter.apply(value)?;
        }
        Ok(value)
    }
}
```

**JMESPath options:**
1. `jmespath` crate - exists but less maintained
2. `jmespatch` crate - alternative implementation
3. Implement core subset (paths, wildcards, filters) manually

### Phase 5: Pipeline & Analysis
**Estimated: 2 story points**

Orchestration and token analysis.

- [x] Pipeline struct connecting parse → filter → encode
- [ ] Token counting (`tiktoken-rs` or `tokenizers`)
- [ ] Analysis mode comparing formats
- [ ] Format auto-selection

```rust
// crates/llm-fmt-core/src/pipeline.rs
pub struct Pipeline {
    parser: Box<dyn Parser>,
    filters: FilterChain,
    encoder: Box<dyn Encoder>,
}

impl Pipeline {
    pub fn run(&self, input: &[u8]) -> Result<String> {
        let parsed = self.parser.parse(input)?;
        let filtered = self.filters.apply(parsed)?;
        self.encoder.encode(&filtered)
    }
}
```

### Phase 6: PyO3 Bindings
**Estimated: 3 story points**

Expose Rust to Python with ergonomic API.

- [x] PyO3 module setup with maturin (PyO3 0.27 for Python 3.14 support)
- [x] Expose `convert()` function
- [ ] Expose `analyze()` function
- [ ] Config struct with Python dict conversion
- [x] Error conversion to Python exceptions
- [ ] Type stubs (`.pyi` files)

```rust
// crates/llm-fmt-py/src/lib.rs
use pyo3::prelude::*;
use llm_fmt_core::{Pipeline, PipelineBuilder, Config};

#[pyfunction]
#[pyo3(signature = (input, /, format="toon", input_format="auto", **kwargs))]
fn convert(
    py: Python<'_>,
    input: &[u8],
    format: &str,
    input_format: &str,
    kwargs: Option<&PyDict>,
) -> PyResult<String> {
    let config = Config::from_pydict(kwargs)?;
    let pipeline = PipelineBuilder::new()
        .input_format(input_format)
        .output_format(format)
        .config(config)
        .build()?;

    pipeline.run(input).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}

#[pymodule]
fn _native(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(convert, m)?)?;
    m.add_function(wrap_pyfunction!(analyze, m)?)?;
    Ok(())
}
```

### Phase 7: Python Wrapper & CLI
**Estimated: 2 story points**

Thin Python layer maintaining current API.

- [x] Update `__init__.py` to import from `_native`
- [x] Keep Click CLI, call Rust functions
- [x] Python implementation deleted - Rust is primary
- [ ] Type stubs for Python API

```python
# python/llm_fmt/__init__.py
try:
    from llm_fmt._native import convert, analyze, Pipeline
    RUST_AVAILABLE = True
except ImportError:
    from llm_fmt._fallback import convert, analyze, Pipeline
    RUST_AVAILABLE = False

__all__ = ["convert", "analyze", "Pipeline", "RUST_AVAILABLE"]
```

### Phase 8: Testing & Benchmarks
**Estimated: 2 story points**

Ensure correctness and measure performance.

- [ ] Port existing Python tests to also run against Rust
- [ ] Property-based tests (Rust: `proptest`, Python: `hypothesis`)
- [ ] Benchmark suite comparing Python vs Rust
- [ ] Cross-platform CI (Linux, macOS, Windows)

```rust
// Benchmark example
#[bench]
fn bench_toon_encode_1000_objects(b: &mut Bencher) {
    let data = generate_uniform_array(1000, 10);
    let encoder = ToonEncoder::new();
    b.iter(|| encoder.encode(&data));
}
```

## Rust Dependencies

```toml
# crates/llm-fmt-core/Cargo.toml
[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
serde_yaml = "0.9"
quick-xml = { version = "0.31", features = ["serialize"] }
csv = "1"
indexmap = { version = "2", features = ["serde"] }
thiserror = "1"
tiktoken-rs = "0.5"  # or tokenizers = "0.15"

[dev-dependencies]
proptest = "1"
criterion = "0.5"

# crates/llm-fmt-py/Cargo.toml
[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
llm-fmt-core = { path = "../llm-fmt-core" }
```

## Build Configuration

```toml
# pyproject.toml
[build-system]
requires = ["maturin>=1.4,<2.0"]
build-backend = "maturin"

[tool.maturin]
features = ["pyo3/extension-module"]
python-source = "python"
module-name = "llm_fmt._native"
```

## Migration Strategy

1. **Parallel development**: Keep current Python code working while building Rust
2. **Feature parity tests**: Same test cases must pass for both implementations
3. **Gradual rollout**: Ship with `RUST_AVAILABLE` flag, fallback to Python
4. **Performance validation**: Benchmarks must show improvement before switching default

## Acceptance Criteria

- [ ] `cargo test` passes all Rust tests
- [ ] `uv run pytest` passes all Python tests using Rust backend
- [ ] Benchmark shows 5-50x speedup on encoding
- [ ] `maturin build` produces wheels for Linux/macOS/Windows
- [ ] Python API unchanged (backward compatible)
- [ ] Falls back to Python if Rust module unavailable
- [ ] CI builds and tests on all platforms

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| JMESPath crate immature | Implement subset manually or use simpler path syntax |
| PyO3 complexity | Start with minimal API, expand incrementally |
| Cross-platform builds | Use maturin + GitHub Actions matrix |
| tiktoken-rs compatibility | Validate token counts match Python tiktoken |

## Success Metrics

- **Encoding speed**: 10x+ improvement for TOON/TSV on 10K+ object arrays
- **Memory usage**: Lower peak memory for large files
- **Startup time**: Not a regression (PyO3 adds some overhead)
- **Wheel size**: < 5MB per platform

## Notes

- Consider also shipping standalone Rust CLI (`cargo install llm-fmt`) as separate optional deliverable
- JMESPath is the highest-risk component; may need to evaluate alternatives
- tiktoken-rs uses same BPE files as Python tiktoken, should produce identical counts
