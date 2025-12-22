# Roadmap

This document outlines the development phases and tasks for llm-fmt.

## Overview

```
Phase 1: MVP (Core Functionality)          23 SP
Phase 2: Filtering & Analysis              19 SP
Phase 3: Auto-Selection & Polish           28 SP
Phase 4: Performance & Extensions          ~30 SP (partially specified)
Phase 5: Ecosystem Integration             ~20 SP (partially specified)
```

## Phase 1: MVP (Core Functionality)

**Goal**: Working CLI that converts JSON to multiple output formats via uvx.

| Task | File | Priority | SP |
|------|------|----------|-----|
| Project scaffolding | [001-project-setup.md](.tasks/001-project-setup.md) | +200 | 3 |
| JSON input parsing | [002-json-input.md](.tasks/002-json-input.md) | +200 | 3 |
| TOON output format | [003-toon-output.md](.tasks/003-toon-output.md) | +300 | 5 |
| Compact JSON output | [004-compact-json-output.md](.tasks/004-compact-json-output.md) | +100 | 2 |
| YAML output format | [005-yaml-output.md](.tasks/005-yaml-output.md) | +100 | 3 |
| CLI interface (Click) | [006-cli-interface.md](.tasks/006-cli-interface.md) | +200 | 5 |
| Stdin/stdout piping | [007-stdin-stdout.md](.tasks/007-stdin-stdout.md) | +150 | 2 |

**Milestone**: `uvx llm-fmt input.json --format toon` works

## Phase 2: Filtering & Analysis

**Goal**: Filter data before conversion, analyze token usage.

| Task | File | Priority | SP |
|------|------|----------|-----|
| dpath filtering (--filter) | [008-dpath-filtering.md](.tasks/008-dpath-filtering.md) | +200 | 5 |
| Max depth limiting | [009-max-depth.md](.tasks/009-max-depth.md) | +100 | 3 |
| Field exclusion (--exclude) | [010-field-exclusion.md](.tasks/010-field-exclusion.md) | +80 | 3 |
| Token counting integration | [011-token-counting.md](.tasks/011-token-counting.md) | +150 | 3 |
| Analysis mode (--analyze) | [012-analysis-mode.md](.tasks/012-analysis-mode.md) | +150 | 5 |

**Milestone**: Filtering reduces output, `--analyze` shows token comparison

## Phase 3: Auto-Selection & Polish

**Goal**: Smart format selection, production-ready CLI.

| Task | File | Priority | SP |
|------|------|----------|-----|
| Data shape detection | [013-data-shape-detection.md](.tasks/013-data-shape-detection.md) | +120 | 5 |
| Auto format selection | [014-auto-format.md](.tasks/014-auto-format.md) | +120 | 3 |
| TSV output (flat arrays) | [015-tsv-output.md](.tasks/015-tsv-output.md) | +50 | 3 |
| Error handling & validation | [016-error-handling.md](.tasks/016-error-handling.md) | -100 | 3 |
| Configuration file support | [017-config-file.md](.tasks/017-config-file.md) | +40 | 3 |
| Comprehensive test suite | [018-test-suite.md](.tasks/018-test-suite.md) | -150 | 8 |
| PyPI packaging & release | [019-pypi-release.md](.tasks/019-pypi-release.md) | +200 | 3 |

**Milestone**: v0.1.0 release on PyPI, installable via uvx

## Phase 4: Performance & Extensions

**Goal**: Rust acceleration, additional input formats, truncation.

| Task | File | Priority | SP |
|------|------|----------|-----|
| YAML input support | [020-yaml-input.md](.tasks/020-yaml-input.md) | +60 | 3 |
| XML input support | [021-xml-input.md](.tasks/021-xml-input.md) | +40 | 5 |
| Truncation strategies | [022-truncation.md](.tasks/022-truncation.md) | +100 | 5 |
| Rust core via PyO3 | [023-rust-core.md](.tasks/023-rust-core.md) | +80 | 13 |
| Streaming large files | [024-streaming.md](.tasks/024-streaming.md) | +60 | 5 |
| Benchmarking suite | [025-benchmarks.md](.tasks/025-benchmarks.md) | -50 | 3 |

**Milestone**: v0.2.0 with YAML/XML input, optional Rust backend

## Phase 5: Ecosystem Integration

**Goal**: Integration with LLM frameworks and tooling.

| Task | File | Priority | SP |
|------|------|----------|-----|
| Python API refinement | [026-python-api.md](.tasks/026-python-api.md) | +100 | 5 |
| LangChain integration | [027-langchain.md](.tasks/027-langchain.md) | +80 | 5 |
| LlamaIndex integration | [028-llamaindex.md](.tasks/028-llamaindex.md) | +50 | 5 |
| LLMLingua integration | [029-llmlingua.md](.tasks/029-llmlingua.md) | +40 | 5 |
| MCP tool wrapper | [030-mcp-tool.md](.tasks/030-mcp-tool.md) | +100 | 3 |

**Milestone**: Drop-in integration for major agent frameworks

---

## Priority Legend

Priority uses business value scoring (-1000 to +1000):

- **Positive (+)**: Adding new value/features
- **Negative (-)**: Fixing negative impact (bugs, poor UX, technical debt)

| Range | Meaning |
|-------|---------|
| +200 to +300 | Critical features, key differentiators |
| +100 to +199 | Important features, good value |
| +40 to +99 | Nice to have, moderate value |
| -50 to -100 | Quality/stability fixes |
| -150 | Critical quality requirements |

## Storypoints

Complexity/effort estimation using Fibonacci sequence (1, 2, 3, 5, 8, 13, 21...)

## Current Status

```
[ ] Phase 1: MVP
[ ] Phase 2: Filtering & Analysis
[ ] Phase 3: Auto-Selection & Polish
[ ] Phase 4: Performance & Extensions
[ ] Phase 5: Ecosystem Integration
```

## Version Targets

| Version | Phase | Key Features |
|---------|-------|--------------|
| 0.1.0 | 1-3 | Core conversion, filtering, analysis, auto-select |
| 0.2.0 | 4 | YAML/XML input, truncation, performance |
| 0.3.0 | 5 | Framework integrations |
| 1.0.0 | - | Stable API, Rust backend, production hardened |

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| TBD | Use Click for CLI | Industry standard, good UX, completion support |
| TBD | orjson for JSON parsing | 10-20x faster than stdlib, Rust-backed |
| TBD | dpath for filtering | Mature, glob syntax familiar to users |
| TBD | tiktoken for token counting | OpenAI's tokenizer, accurate for GPT models |
| TBD | maturin for Rust build | Best PyO3 integration, handles wheels |
