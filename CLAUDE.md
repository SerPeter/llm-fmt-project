# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

llm-fmt is a token-efficient data format converter for LLM and agent contexts. It converts JSON, YAML, and XML to optimized formats (TOON, compact JSON, YAML, TSV) that reduce token consumption by 30-60% when passing structured data to LLMs.

**Status**: Early development - source code not yet implemented. Task specifications in `.tasks/` directory define the implementation plan.

## Commands

```bash
# Install dependencies
uv sync

# Run CLI
uv run llm-fmt --help

# Run tests
uv run pytest
uv run pytest tests/test_cli.py::test_specific  # single test

# Lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type checking
uv run mypy src/

# Build
uv build
```

## Architecture

### Planned Source Structure
```
src/llm_fmt/
├── cli.py              # Click CLI entry point
├── convert.py          # Format conversion orchestration
├── parsers.py          # JSON/YAML/XML input parsing
├── filter.py           # dpath-based filtering (--filter, --exclude, --max-depth)
├── detect.py           # Data shape detection for auto-format selection
├── analyze.py          # Token analysis and format recommendations
├── tokens.py           # tiktoken integration for token counting
└── formats/
    ├── toon.py         # TOON encoding (best for uniform arrays)
    ├── compact_json.py # Minified JSON output
    └── yaml_fmt.py     # YAML output
```

### Output Formats
- **TOON**: Tabular format for uniform arrays (30-60% savings)
- **Compact JSON**: Minified JSON (10-20% savings)
- **YAML**: Human-readable (20-40% savings)
- **TSV**: Tab-separated for flat data (40-50% savings)

### Key Dependencies
- `click`: CLI framework
- `orjson`: Fast JSON parsing
- `pyyaml`: YAML output
- `dpath`: Path-based filtering
- `tiktoken`: Token counting (optional)

## Development Phases

Task files in `.tasks/` contain detailed specifications:
- **Phase 1** (001-007): MVP - core format conversion
- **Phase 2** (008-012): Filtering and token analysis
- **Phase 3** (013-019): Auto-format selection, tests, PyPI release
- **Phase 4** (020-025): YAML/XML input, Rust acceleration, streaming
- **Phase 5** (026-030): LangChain/LlamaIndex/MCP integrations

## Code Style

- **Python**: 3.14+ (configured in pyproject.toml)
- **Formatter/Linter**: Ruff (see `ruff.toml`)
- **Line length**: 120
- **Quotes**: Double
- **Docstrings**: Google convention
