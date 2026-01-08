# llm-fmt

**Token-efficient data format converter for LLM and agent contexts**

Convert JSON, YAML, XML, and CSV to optimized formats that reduce token consumption by 30-70% when passing structured data to LLMs. Includes filtering, truncation, analysis, and automatic format selection based on data shape.

## Why?

Every brace, quote, and repeated key in JSON translates to tokens billed. When building agent systems that process tool outputs and API responses, format choice directly impacts costs and context window usage.

```bash
# A 10KB JSON API response might use 3,000 tokens
# The same data in TSV format: ~1,000 tokens
# With filtering applied: potentially under 500 tokens
```

This tool sits at the boundary between your data sources and LLM consumption, optimizing the representation automatically. It works with any structured output—API responses, CLI tools that emit JSON, database queries, or configuration files.

## Features

- **Multi-format input**: JSON, YAML, XML, CSV (auto-detected)
- **Multi-format output**: TOON, compact JSON, YAML, TSV, CSV
- **Smart auto-selection**: Analyzes data shape and picks optimal format
- **Filtering**: Path expressions, max-depth limits, field exclusion
- **Truncation**: Head/tail/sample/balanced strategies with preserve paths
- **Token analysis**: Compare token counts across formats before choosing
- **Configuration**: Hierarchical config (CLI > env vars > config files > defaults)
- **Pipe-friendly**: Works seamlessly in shell pipelines
- **Fast**: Rust core with Python bindings via PyO3

## Installation

```bash
pip install llm-file-format
# or
uv tool install llm-file-format
```

After installation, use the `llm-fmt` command. Without installing:

```bash
uvx --from llm-file-format llm-fmt data.json
```

## Quick Start

```bash
# Convert JSON to TOON (default format)
llm-fmt data.json

# Specify output format
llm-fmt data.json -f yaml
llm-fmt data.json -f tsv

# Filter specific paths
llm-fmt data.json -i "users[*].name"

# Limit array sizes and string lengths
llm-fmt data.json --max-items 10 --max-string-length 100

# Analyze token usage across all formats
llm-fmt data.json --analyze

# Pipe from API response
curl -s api.example.com/users | llm-fmt -f toon

# Limit nesting depth
llm-fmt complex.json --max-depth 2 -f yaml

# Show resolved configuration
llm-fmt --show-config
```

## Output Formats

| Format | Best For | Typical Savings |
|--------|----------|-----------------|
| `tsv` | Flat tabular data, uniform arrays | 60-75% |
| `toon` | Uniform arrays of objects (logs, records, API lists) | 45-60% |
| `csv` | Tabular data with special characters | 50-60% |
| `yaml` | Nested configs, key-value pairs | 25-35% |
| `json` | Compatibility, deeply nested/mixed structures | 10-15% |

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

## Filtering & Truncation

```bash
# Filter specific paths (bracket notation)
llm-fmt data.json -i "users[*].name"
llm-fmt data.json -i "results[0].data"

# Limit nesting depth
llm-fmt data.json --max-depth 3

# Truncate large arrays
llm-fmt data.json --max-items 50

# Truncation strategies
llm-fmt data.json --max-items 10 --truncation-strategy head      # first N items
llm-fmt data.json --max-items 10 --truncation-strategy tail      # last N items
llm-fmt data.json --max-items 10 --truncation-strategy balanced  # start + end
llm-fmt data.json --max-items 10 --truncation-strategy sample    # random sample

# Preserve specific paths from truncation
llm-fmt data.json --max-items 5 --preserve "errors" --preserve "metadata"

# Truncate long strings
llm-fmt data.json --max-string-length 200
```

## Token Analysis

Compare token counts across formats to make informed decisions:

```bash
$ llm-fmt large-response.json --analyze

Format Analysis:
────────────────────────────────────────────
Original JSON:     3,247 tokens (100.0%)
Compact JSON:      2,891 tokens (89.0%)
YAML:              2,156 tokens (66.4%)
TOON:              1,342 tokens (41.3%)
TSV:               1,102 tokens (33.9%)  ← recommended

Data shape: uniform_array
Recommendation: tsv
```

## Configuration

llm-fmt uses a hierarchical configuration system:

1. **CLI arguments** (highest priority)
2. **Environment variables** (`LLM_FMT_*` prefix)
3. **Config files** (`.llm-fmt.yaml`, `.llm-fmt.toml`)
4. **pyproject.toml** (`[tool.llm-fmt]` section)
5. **Strong defaults** (lowest priority)

### Config File Example

Create `.llm-fmt.yaml` in your project:

```yaml
defaults:
  format: toon
  input_format: auto

limits:
  max_tokens: 10000    # ~10% of 100K context window
  max_items: 500
  max_string_length: 500
  max_depth: 8

truncation:
  strategy: head
  show_summary: true

filter:
  default_exclude:
    - _metadata
    - _links
    - debug

output:
  strict: false        # Set true to error instead of truncating
```

### Environment Variables

```bash
export LLM_FMT_FORMAT=toon
export LLM_FMT_MAX_TOKENS=5000
export LLM_FMT_MAX_ITEMS=100
export LLM_FMT_STRICT=true
export LLM_FMT_DEFAULT_EXCLUDE="_metadata,_links,debug"
```

### Strict Mode

Use `--strict` to error instead of silently truncating:

```bash
$ llm-fmt huge-response.json --strict --max-items 10
Error: Output exceeds max_items limit (1000 > 10 items)
Hint: Use --max-items to increase limit, or remove --strict to allow truncation
```

## Python API

```python
from llm_fmt import convert, analyze, detect_shape, select_format

# Basic conversion
result = convert(data, format="toon")

# With options
result = convert(
    data,
    format="yaml",
    max_depth=3,
    max_items=100,
    max_string_length=200,
)

# Auto-select format based on data shape
shape = detect_shape(data)
best_format = select_format(data)
result = convert(data, format=best_format)

# Analysis (returns dict or formatted string)
report = analyze(data, output_json=True)
print(f"Recommended: {report['recommendation']}")
print(f"Savings: {report['formats']['toon']['savings_percent']}%")
```

## Requirements

- Python 3.10+
- Rust toolchain (for building from source)

Runtime dependencies:
- `click` - CLI framework
- `pyyaml` - YAML config file support

## Development

```bash
# Clone and install in development mode
git clone https://github.com/SerPeter/llm-fmt-project
cd llm-fmt
uv sync

# Build Rust extension
maturin develop

# Run tests
uv run pytest

# Run Rust tests
cargo test -p llm-fmt-core

# Run CLI locally
uv run llm-fmt --help

# Run benchmarks
cargo bench
cargo run --release --bin benchreport
```

## Architecture

llm-fmt has a Rust core (`llm-fmt-core`) with Python bindings via PyO3:

```
crates/
├── llm-fmt-core/     # Rust library: parsers, encoders, filters, pipeline
└── llm-fmt-py/       # PyO3 bindings exposing Rust to Python

src/llm_fmt/
├── __init__.py       # Python API (wraps Rust functions)
├── cli.py            # Click CLI
└── config.py         # Configuration system
```

The Rust core handles all data processing:
- **Parsers**: JSON, YAML, XML, CSV (auto-detection)
- **Encoders**: TOON, JSON, YAML, TSV, CSV
- **Filters**: Include paths, max depth, truncation
- **Analysis**: Data shape detection, token estimation, format recommendation

## Benchmarks

Token counts use heuristic estimation (~94% accuracy vs tiktoken).

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

## Claude Code Integration

llm-fmt includes a skill file for [Claude Code](https://claude.ai/code) integration.

**Install the skill:**
```bash
# macOS/Linux
cp llm-fmt.skill.md ~/.claude/skills/

# Windows
copy llm-fmt.skill.md %USERPROFILE%\.claude\skills\
```

**Add to `~/.claude/settings.json` to allow without prompts:**
```json
{
  "permissions": {
    "allow": [
      "Bash(llm-fmt:*)"
    ]
  }
}
```

## Related Projects

- [toon-format](https://github.com/toon-format/toon) - TOON specification and reference implementation
- [LLMLingua](https://github.com/microsoft/LLMLingua) - ML-based prompt compression

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
