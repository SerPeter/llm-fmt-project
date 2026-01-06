# llm-fmt

**Token-efficient data format converter for LLM and agent contexts**

Convert JSON, YAML, and XML to optimized formats that reduce token consumption by 30-60% when passing structured data to LLMs. Includes filtering, analysis, and automatic format selection based on data shape.

## Why?

Every brace, quote, and repeated key in JSON translates to tokens billed. When building agent systems that process tool outputs and API responses, format choice directly impacts costs and context window usage.

```bash
# A 10KB JSON API response might use 3,000 tokens
# The same data in TOON format: ~1,200 tokens
# With filtering applied: potentially under 500 tokens
```

This tool sits at the boundary between your data sources and LLM consumption, optimizing the representation automatically. It works with any structured output—API responses, CLI tools that emit JSON, database queries, or configuration files.

## Features

- **Multi-format output**: TOON, compact JSON, YAML, TSV (for flat data)
- **Smart auto-selection**: Analyzes data shape and picks optimal format
- **Filtering**: dpath-style glob patterns, max-depth limits, field exclusion
- **Token analysis**: Compare token counts across formats before choosing
- **Truncation**: Smart truncation strategies for large outputs
- **Pipe-friendly**: Works seamlessly in shell pipelines
- **Fast**: Uses orjson for JSON parsing, with optional Rust acceleration

## Installation

```bash
# With uv (recommended)
uv tool install llm-fmt

# Or run directly without installing
uvx llm-fmt input.json --format toon

# With pip
pip install llm-fmt
```

## Quick Start

```bash
# Convert JSON to TOON (best for uniform arrays)
llm-fmt data.json --format toon

# Auto-select optimal format based on data structure
llm-fmt data.json --auto

# Filter before conversion (compound savings)
llm-fmt data.json --filter "users/*/email,name" --format toon

# Analyze token usage across all formats
llm-fmt data.json --analyze

# Pipe from API response
curl -s api.example.com/users | llm-fmt --format toon

# Limit nesting depth
llm-fmt complex.json --max-depth 2 --format yaml
```

## Output Formats

| Format | Best For | Typical Savings |
|--------|----------|-----------------|
| `toon` | Uniform arrays of objects (logs, records, API lists) | 30-60% |
| `compact-json` | Deeply nested configs, mixed structures | 10-20% |
| `yaml` | Key-value pairs, readable configs | 20-40% |
| `tsv` | Flat arrays, tabular data | 40-50% |

### Format Examples

**Input JSON:**
```json
{
  "users": [
    {"id": 1, "name": "Alice", "role": "admin"},
    {"id": 2, "name": "Bob", "role": "user"}
  ]
}
```

**TOON output:**
```
users[2]{id,name,role}:
  1,Alice,admin
  2,Bob,user
```

**Compact JSON output:**
```json
{"users":[{"id":1,"name":"Alice","role":"admin"},{"id":2,"name":"Bob","role":"user"}]}
```

## Filtering

Filter data before format conversion to compound token savings:

```bash
# Select specific paths (dpath glob syntax)
llm-fmt data.json --filter "users/*/name"
llm-fmt data.json --filter "results/**/id"      # recursive

# Exclude fields
llm-fmt data.json --exclude "_metadata,internal,debug"

# Limit nesting depth
llm-fmt data.json --max-depth 3

# Combine filters
llm-fmt api-response.json \
  --filter "data/items/*" \
  --exclude "created_at,updated_at,_links" \
  --max-depth 2 \
  --format toon
```

## Token Analysis

Compare token counts across formats to make informed decisions:

```bash
$ llm-fmt large-response.json --analyze

Format Analysis (using cl100k_base tokenizer):
──────────────────────────────────────────────
Original JSON:     3,247 tokens (100%)
Compact JSON:      2,891 tokens (89%)
YAML:              2,156 tokens (66%)
TOON:              1,342 tokens (41%)  ← recommended

Data shape: uniform array of 150 objects with 8 fields
Recommendation: TOON (saves 1,905 tokens per call)
```

## Auto Mode

Let the tool analyze your data and pick the optimal format:

```bash
$ llm-fmt data.json --auto

# Decision logic:
# - Uniform array of objects → TOON
# - Flat key-value pairs → YAML
# - Deeply nested/mixed → compact-json
# - Simple flat array → TSV
```

## Truncation (Large Outputs)

For outputs exceeding token budgets:

```bash
# Truncate to fit token budget
llm-fmt huge-response.json --max-tokens 4000

# Truncation strategies
llm-fmt data.json --max-tokens 2000 --truncate middle  # preserve start/end
llm-fmt data.json --max-tokens 2000 --truncate end     # keep beginning
llm-fmt data.json --max-tokens 2000 --truncate sample  # representative sample
```

## Python API

```python
from llm_fmt import convert, analyze, Filter

# Basic conversion
toon_output = convert(data, format="toon")

# With filtering
filtered = convert(
    data,
    format="auto",
    filter=Filter(
        include=["users/*/email", "users/*/name"],
        exclude=["_metadata"],
        max_depth=3
    )
)

# Analysis
report = analyze(data)
print(f"Best format: {report.recommended}")
print(f"Token savings: {report.savings_percent}%")
```

## Configuration

Create `.llm-fmt.toml` in your project or home directory:

```toml
[defaults]
format = "auto"
tokenizer = "cl100k_base"  # or "o200k_base" for GPT-4o

[filter]
default_exclude = ["_metadata", "_links", "debug"]
default_max_depth = 5

[analysis]
show_recommendations = true
```

## Requirements

- Python 3.10+
- Dependencies:
  - `click` - CLI framework
  - `orjson` - Fast JSON parsing
  - `pyyaml` - YAML output
  - `dpath` - Path-based filtering
  - `tiktoken` - Token counting (optional, for analysis)
  - `toon-format` - TOON encoding

## Development

```bash
# Clone and install in development mode
git clone https://github.com/youruser/llm-fmt
cd llm-fmt
uv sync

# Run tests
uv run pytest

# Run CLI locally
uv run llm-fmt --help
```

## Benchmarks

Benchmarks run on synthetic data with realistic shapes. Token counts use heuristic estimation (~94% accuracy vs tiktoken).

### Token Savings by Format

**Uniform Arrays (API Response style - 1K objects):**

| Format | Tokens | Savings | Encoding Time |
|--------|--------|---------|---------------|
| Input JSON | 63,160 | - | - |
| TSV | 24,162 | **61.7%** | 951µs |
| CSV | 31,169 | 50.6% | 796µs |
| TOON | 33,172 | 47.5% | 521µs |
| YAML | 45,150 | 28.5% | 776µs |
| Compact JSON | 57,151 | 9.5% | 305µs |

**Tabular Data (1K rows):**

| Format | Tokens | Savings | Encoding Time |
|--------|--------|---------|---------------|
| Input JSON | 39,620 | - | - |
| TSV | 10,590 | **73.3%** | 804µs |
| TOON | 15,598 | 60.6% | 506µs |
| CSV | 15,595 | 60.6% | 848µs |
| YAML | 27,580 | 30.4% | 701µs |
| Compact JSON | 35,581 | 10.2% | 310µs |

**Nested Config (depth 20):**

| Format | Tokens | Savings |
|--------|--------|---------|
| Input JSON | 61,700 | - |
| YAML | 41,596 | **32.6%** |
| Compact JSON | 53,322 | 13.6% |

### Format Selection Guide

| Data Shape | Recommended | Typical Savings |
|------------|-------------|-----------------|
| Uniform arrays (logs, API lists) | TSV or TOON | 50-70% |
| Tabular/flat data | TSV | 70-75% |
| Mixed/sparse arrays | TOON | 40-50% |
| Deeply nested configs | YAML | 30-35% |
| Complex mixed structures | Compact JSON | 10-15% |

### Encoding Performance (Rust core, 10K objects)

| Encoder | Time | Throughput |
|---------|------|------------|
| JSON | 5.7ms | 280 MiB/s |
| TOON | 8.8ms | 181 MiB/s |
| YAML | 9.7ms | 164 MiB/s |
| TSV | 11.4ms | 140 MiB/s |
| CSV | 8.5ms | 188 MiB/s |

Run benchmarks locally:
```bash
# Quick summary with token savings
cargo run --release --bin benchreport

# Full Criterion benchmark suite
cargo bench
```

## Related Projects

- [toon-format](https://github.com/toon-format/toon) - TOON specification and reference implementation
- [LLMLingua](https://github.com/microsoft/LLMLingua) - ML-based prompt compression
- [orjson](https://github.com/ijl/orjson) - Fast JSON library for Python

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
