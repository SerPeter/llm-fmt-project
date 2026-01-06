# Task 025: Rust Benchmarks

**Phase**: 4 - Performance & Extensions
**Priority**: +75
**Storypoints**: 5
**Status**: [x] Complete

## Objective

Create a comprehensive benchmark suite for the Rust core to measure performance characteristics and validate token savings claims. Benchmarks focus on real-world scenarios with synthetic data of realistic shapes.

## Key Metrics

For each benchmark, measure:
1. **Output tokens** - Token count using tiktoken/tokenizers
2. **Token savings %** - Reduction compared to original input format
3. **Peak memory** - Maximum heap allocation during conversion
4. **Total time** - Wall-clock time for the operation

## Directory Structure

```
data/benchmark/
├── json/
│   ├── api_response_small.json    # ~100 uniform objects (API-like)
│   ├── api_response_medium.json   # ~1K uniform objects
│   ├── api_response_large.json    # ~10K uniform objects
│   ├── nested_config.json         # Deep nesting (5-10 levels)
│   ├── mixed_types.json           # Varied value types
│   └── sparse_array.json          # Non-uniform objects
├── yaml/
│   ├── config_small.yaml
│   ├── config_medium.yaml
│   └── config_large.yaml
├── xml/
│   ├── feed_small.xml
│   ├── feed_medium.xml
│   └── feed_large.xml
└── csv/
    ├── tabular_small.csv          # ~100 rows
    ├── tabular_medium.csv         # ~1K rows
    └── tabular_large.csv          # ~10K rows

crates/llm-fmt-core/benches/
├── encoding.rs      # All encoders at various data sizes
├── parsing.rs       # All parsers at various data sizes
├── pipeline.rs      # End-to-end conversions
├── filters.rs       # Filter operations
└── common/
    └── mod.rs       # Shared utilities, data loading
```

## Implementation

### Benchmark Harness

Use Criterion for micro-benchmarks with custom reporting for the key metrics.

```toml
# crates/llm-fmt-core/Cargo.toml
[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
peak_alloc = "0.2"

[[bench]]
name = "encoding"
harness = false

[[bench]]
name = "parsing"
harness = false

[[bench]]
name = "pipeline"
harness = false

[[bench]]
name = "filters"
harness = false
```

### Data Generators

Create a `benchgen` binary or build script to generate synthetic benchmark data:

```rust
// Shape: API response with uniform objects
fn generate_api_response(count: usize) -> Value {
    Value::Array((0..count).map(|i| {
        Value::Object(indexmap! {
            "id".into() => Value::Number(i.into()),
            "name".into() => Value::String(format!("User {}", i)),
            "email".into() => Value::String(format!("user{}@example.com", i)),
            "active".into() => Value::Bool(i % 2 == 0),
            "score".into() => Value::Number((i * 17 % 100).into()),
            "created_at".into() => Value::String("2024-01-15T10:30:00Z".into()),
        })
    }).collect())
}

// Shape: Deeply nested config
fn generate_nested_config(depth: usize) -> Value {
    fn nest(level: usize, max: usize) -> Value {
        if level >= max {
            Value::String("leaf".into())
        } else {
            Value::Object(indexmap! {
                "level".into() => Value::Number(level.into()),
                "config".into() => Value::Object(indexmap! {
                    "enabled".into() => Value::Bool(true),
                    "value".into() => Value::Number((level * 10).into()),
                }),
                "child".into() => nest(level + 1, max),
            })
        }
    }
    nest(0, depth)
}

// Shape: Mixed/heterogeneous data
fn generate_mixed_types(count: usize) -> Value {
    // Arrays with varying object shapes, null values, nested arrays
}

// Shape: Sparse array (non-uniform objects)
fn generate_sparse_array(count: usize) -> Value {
    // Objects with different field sets
}
```

### Encoding Benchmarks

```rust
// benches/encoding.rs
use criterion::{criterion_group, criterion_main, Criterion, BenchmarkId};
use llm_fmt_core::encoders::*;
use llm_fmt_core::Value;

fn bench_toon_encoding(c: &mut Criterion) {
    let mut group = c.benchmark_group("toon_encode");

    for size in [100, 1000, 10000] {
        let data = load_benchmark_data(&format!("json/api_response_{}.json", size_name(size)));

        group.bench_with_input(
            BenchmarkId::new("api_response", size),
            &data,
            |b, data| {
                let encoder = ToonEncoder::new();
                b.iter(|| encoder.encode(data))
            },
        );
    }
    group.finish();
}

fn bench_all_encoders(c: &mut Criterion) {
    let mut group = c.benchmark_group("encoder_comparison");
    let data = load_benchmark_data("json/api_response_medium.json");

    for (name, encoder) in [
        ("toon", Box::new(ToonEncoder::new()) as Box<dyn Encoder>),
        ("json", Box::new(CompactJsonEncoder::new())),
        ("yaml", Box::new(YamlEncoder::new())),
        ("tsv", Box::new(TsvEncoder::new())),
    ] {
        group.bench_with_input(
            BenchmarkId::new(name, "1k_objects"),
            &data,
            |b, data| b.iter(|| encoder.encode(data)),
        );
    }
    group.finish();
}

criterion_group!(benches, bench_toon_encoding, bench_all_encoders);
criterion_main!(benches);
```

### Memory Tracking

```rust
use peak_alloc::PeakAlloc;

#[global_allocator]
static PEAK_ALLOC: PeakAlloc = PeakAlloc;

fn measure_peak_memory<F, R>(f: F) -> (R, usize)
where
    F: FnOnce() -> R,
{
    PEAK_ALLOC.reset_peak_usage();
    let result = f();
    let peak = PEAK_ALLOC.peak_usage_as_kb();
    (result, peak)
}
```

### Token Counting

Integrate with the existing `tokens.rs` module or add tiktoken-rs:

```rust
use tiktoken_rs::cl100k_base;

fn count_tokens(text: &str) -> usize {
    let bpe = cl100k_base().unwrap();
    bpe.encode_with_special_tokens(text).len()
}

fn calculate_savings(original: &str, converted: &str) -> f64 {
    let orig_tokens = count_tokens(original);
    let conv_tokens = count_tokens(converted);
    ((orig_tokens - conv_tokens) as f64 / orig_tokens as f64) * 100.0
}
```

### Summary Report

Generate a markdown table after benchmark runs:

```
## Benchmark Results

### Encoding Performance (1K uniform objects)

| Format | Tokens | Savings | Peak Memory | Time |
|--------|--------|---------|-------------|------|
| TOON   | 4,521  | 58.2%   | 2.1 MB      | 12ms |
| YAML   | 6,890  | 36.4%   | 2.3 MB      | 18ms |
| JSON   | 8,234  | 24.1%   | 1.8 MB      | 8ms  |
| TSV    | 3,890  | 64.1%   | 1.5 MB      | 6ms  |

### Scaling Characteristics

| Size   | TOON Time | TOON Memory | TOON Tokens |
|--------|-----------|-------------|-------------|
| 100    | 1.2ms     | 0.3 MB      | 452         |
| 1K     | 12ms      | 2.1 MB      | 4,521       |
| 10K    | 125ms     | 18.5 MB     | 45,210      |
```

## CLI Integration (Future)

After benchmarks are established, add a `--benchmark` flag or separate `llm-fmt-bench` command:

```bash
# Run full benchmark suite
cargo bench

# Quick benchmark of specific file
llm-fmt --benchmark input.json

# Compare all formats for a file
llm-fmt --analyze --benchmark input.json
```

## Acceptance Criteria

- [x] `data/benchmark/` contains synthetic test data for all input formats
- [x] Data generator creates realistic, reproducible test fixtures (`benchgen` binary)
- [x] `cargo bench` runs full Criterion benchmark suite
- [x] Encoding benchmarks cover all output formats (TOON, JSON, YAML, TSV, CSV)
- [x] Parsing benchmarks cover all input formats (JSON, YAML, XML, CSV)
- [x] Pipeline benchmarks measure end-to-end conversion
- [x] `benchreport` binary reports: time, output tokens, savings %
- [x] HTML reports generated in `target/criterion/`
- [ ] CI job runs benchmarks (without regression gating initially)

## Dependencies

- `criterion = "0.5"` - Benchmark framework
- `peak_alloc = "0.2"` - Memory tracking
- `tiktoken-rs = "0.5"` - Token counting (optional, for token metrics)

## Notes

- Start without tiktoken-rs if it complicates the build; add token counting later
- Focus on relative comparisons between formats rather than absolute numbers
- Use `--save-baseline` in CI to track performance over time
- Consider `iai` crate for instruction-count-based benchmarks (more stable than wall-clock)
- Python CLI startup optimization is a separate follow-up task (026)
