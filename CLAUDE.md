# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

llm-fmt is a token-efficient data format converter for LLM and agent contexts. It converts JSON, YAML, XML, and CSV to optimized formats (TOON, compact JSON, YAML, TSV, CSV) that reduce token consumption by 30-70% when passing structured data to LLMs.

**Status**: Core functionality complete. Rust implementation with PyO3 bindings.

## Commands

```bash
# Install dependencies
uv sync

# Build Rust extension
maturin develop

# Run CLI
uv run llm-fmt --help

# Run Python tests
uv run pytest

# Run Rust tests
cargo test -p llm-fmt-core

# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type checking
uv run basedpyright src/

# Run benchmarks
cargo bench
cargo run --release --bin benchreport
```

## Architecture

### Source Structure
```
crates/
├── llm-fmt-core/           # Rust library
│   ├── src/
│   │   ├── lib.rs          # Public API, Value type
│   │   ├── parsers/        # JSON, YAML, XML, CSV parsers
│   │   ├── encoders/       # TOON, JSON, YAML, TSV, CSV encoders
│   │   ├── filters/        # Include, depth, truncation filters
│   │   ├── pipeline.rs     # Pipeline orchestration
│   │   ├── analysis.rs     # Data shape detection
│   │   └── tokens.rs       # Token estimation
│   └── benches/            # Criterion benchmarks
│
└── llm-fmt-py/             # PyO3 bindings

src/llm_fmt/
├── __init__.py             # Python API exports
├── cli.py                  # Click CLI
└── config.py               # Configuration system
```

### Output Formats
- **TSV**: Tab-separated (60-75% savings for tabular data)
- **TOON**: Tabular Object Notation (45-60% savings for uniform arrays)
- **CSV**: Comma-separated (50-60% savings)
- **YAML**: Human-readable (25-35% savings)
- **JSON**: Compact JSON (10-15% savings)

### Key Dependencies

**Rust (core):**
- `serde_json` - JSON parsing
- `serde_yaml` - YAML parsing/encoding
- `quick-xml` - XML parsing
- `csv` - CSV parsing/encoding
- `indexmap` - Ordered maps

**Python (CLI/config):**
- `click` - CLI framework
- `pyyaml` - YAML config file support

## Development Phases

Archived task files in `.tasks/archive/` contain original specifications:
- **Phase 1-4**: Complete (core, filtering, analysis, Rust, config)
- **Phase 5**: Not started (LangChain/LlamaIndex/MCP integrations)

See [ROADMAP.md](ROADMAP.md) for current status.

## Code Style

- **Python**: 3.14+ (configured in pyproject.toml)
- **Rust**: Standard rustfmt
- **Formatter/Linter**: Ruff for Python
- **Line length**: 120
- **Quotes**: Double
