# Roadmap

This document outlines the development phases and current status of llm-fmt.

## Overview

```
Phase 1: MVP (Core Functionality)          ✅ Complete
Phase 2: Filtering & Analysis              ✅ Complete
Phase 3: Auto-Selection & Polish           ✅ Complete
Phase 4: Performance & Extensions          ✅ Complete
Phase 5: Ecosystem Integration             🔲 Not started
```

## Current Status

**Version**: 0.1.0-dev (pre-release)

The core functionality is complete with a Rust implementation:
- Multi-format input (JSON, YAML, XML, CSV) with auto-detection
- Multi-format output (TOON, JSON, YAML, TSV, CSV)
- Filtering (path expressions, max depth)
- Truncation (head/tail/sample/balanced strategies)
- Analysis mode with format recommendations
- Hierarchical configuration system
- Comprehensive benchmark suite

## Phase 1: MVP (Core Functionality) ✅

**Goal**: Working CLI that converts JSON to multiple output formats.

| Task | Status | Description |
|------|--------|-------------|
| Project scaffolding | ✅ | pyproject.toml, uv, directory structure |
| JSON input parsing | ✅ | Parse JSON via serde_json |
| TOON output format | ✅ | Tabular Object Notation encoder |
| Compact JSON output | ✅ | Minified JSON encoder |
| YAML output format | ✅ | YAML encoder via serde_yaml |
| CLI interface | ✅ | Click-based CLI with options |
| Stdin/stdout piping | ✅ | Pipe-friendly I/O |

## Phase 2: Filtering & Analysis ✅

**Goal**: Filter data before conversion, analyze token usage.

| Task | Status | Description |
|------|--------|-------------|
| Path filtering | ✅ | `--filter` / `-i` option |
| Max depth limiting | ✅ | `--max-depth` option |
| Token counting | ✅ | Heuristic token estimation |
| Analysis mode | ✅ | `--analyze` with format comparison |

## Phase 3: Auto-Selection & Polish ✅

**Goal**: Smart format selection, production-ready CLI.

| Task | Status | Description |
|------|--------|-------------|
| Data shape detection | ✅ | Detect uniform/sparse/nested structures |
| Auto format selection | ✅ | `select_format()` recommendations |
| TSV output | ✅ | Tab-separated values encoder |
| CSV output | ✅ | Comma-separated values encoder |
| Error handling | ✅ | Typed errors, clear messages |
| Configuration system | ✅ | Hierarchical config (CLI > env > files > defaults) |
| Test suite | ✅ | 72 tests (Python + Rust) |

## Phase 4: Performance & Extensions ✅

**Goal**: Rust core, additional input formats, truncation.

| Task | Status | Description |
|------|--------|-------------|
| Rust core | ✅ | Full rewrite in Rust with PyO3 bindings |
| YAML input support | ✅ | Parse YAML via serde_yaml |
| XML input support | ✅ | Parse XML via quick-xml |
| CSV input support | ✅ | Parse CSV via csv crate |
| Truncation strategies | ✅ | head/tail/sample/balanced + preserve paths |
| Benchmark suite | ✅ | Criterion benchmarks, benchreport binary |

## Phase 5: Ecosystem Integration 🔲

**Goal**: Integration with LLM frameworks and tooling.

| Task | Status | Description |
|------|--------|-------------|
| Python API refinement | 🔲 | Improve ergonomics, add Filter class |
| LangChain integration | 🔲 | Output parser / tool wrapper |
| LlamaIndex integration | 🔲 | Node parser integration |
| MCP tool wrapper | 🔲 | Model Context Protocol server |
| PyPI release | 🔲 | Publish to PyPI |

## Version Targets

| Version | Status | Key Features |
|---------|--------|--------------|
| 0.1.0 | 🔜 Next | Core conversion, filtering, analysis, config |
| 0.2.0 | Planned | Framework integrations, API refinements |
| 1.0.0 | Planned | Stable API, production hardened |

## Architecture

The project uses a Rust core with Python bindings:

```
crates/
├── llm-fmt-core/     # Rust library (parsers, encoders, filters)
└── llm-fmt-py/       # PyO3 bindings

src/llm_fmt/
├── __init__.py       # Python API exports
├── cli.py            # Click CLI
└── config.py         # Configuration system
```

See [docs/architecture.md](docs/architecture.md) for details.

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026 | Rust core via PyO3 | Performance, memory safety, single codebase |
| 2026 | Click for CLI | Industry standard, good UX |
| 2026 | Hierarchical config | Flexible defaults, env vars, config files |
| 2026 | Heuristic token counting | ~94% accuracy, no external dependencies |
| 2026 | maturin for build | Best PyO3 integration |
