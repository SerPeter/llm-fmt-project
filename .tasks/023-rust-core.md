# Task 023: Rust Core via PyO3

**Phase**: 4 - Performance & Extensions  
**Priority**: +80
**Storypoints**: 13  
**Status**: [ ] Not started

## Objective

Replace performance-critical Python code with Rust via PyO3.

## Requirements

- [ ] Rust implementation of TOON encoding
- [ ] PyO3 bindings for Python interface
- [ ] maturin build system
- [ ] Fallback to pure Python if Rust not available
- [ ] Benchmark showing performance improvement

## Architecture

```
llm-fmt/
├── python/
│   └── llm_fmt/
│       ├── __init__.py
│       └── _fallback.py    # Pure Python fallback
├── src/
│   └── lib.rs              # Rust implementation
├── Cargo.toml
└── pyproject.toml          # maturin config
```

## Expected Performance

Based on similar projects (orjson, pydantic-core):
- 10-50x speedup on encoding
- Reduced memory allocations
- Better cache efficiency

## Acceptance Criteria

- [ ] `maturin build` creates working wheel
- [ ] Benchmark shows measurable improvement
- [ ] Falls back gracefully if Rust not compiled
- [ ] Same API as pure Python version
