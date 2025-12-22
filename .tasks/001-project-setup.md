# Task 001: Project Scaffolding

**Phase**: 1 - MVP  
**Priority**: +200
**Storypoints**: 3  
**Status**: [ ] Not started

## Objective

Set up the project structure with proper Python packaging for uvx/pip installation.

## Requirements

- [ ] Create `pyproject.toml` with project metadata
- [ ] Configure build system (hatchling or maturin)
- [ ] Set up source layout (`src/llm_fmt/`)
- [ ] Define CLI entry point for `llm-fmt` command
- [ ] Add development dependencies (pytest, ruff, mypy)
- [ ] Create `.gitignore` for Python projects
- [ ] Initialize git repository

## Implementation Details

### pyproject.toml

```toml
[project]
name = "llm-fmt"
version = "0.1.0"
description = "Token-efficient data format converter for LLM contexts"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
authors = [{ name = "Your Name", email = "you@example.com" }]
keywords = ["llm", "tokens", "json", "toon", "ai", "agents"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing :: General",
]
dependencies = [
    "click>=8.1",
    "orjson>=3.10",
    "pyyaml>=6.0",
    "dpath>=2.2",
]

[project.optional-dependencies]
analysis = ["tiktoken>=0.7"]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
]
all = ["llm-fmt[analysis,dev]"]

[project.scripts]
llm-fmt = "llm_fmt.cli:main"

[project.urls]
Homepage = "https://github.com/youruser/llm-fmt"
Repository = "https://github.com/youruser/llm-fmt"
Issues = "https://github.com/youruser/llm-fmt/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/llm_fmt"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.10"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=llm_fmt"
```

### Directory Structure

```
llm-fmt/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── src/
│   └── llm_fmt/
│       ├── __init__.py
│       ├── cli.py
│       ├── convert.py
│       ├── formats/
│       │   ├── __init__.py
│       │   ├── toon.py
│       │   ├── compact_json.py
│       │   └── yaml_fmt.py
│       └── filter.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_convert.py
```

## Acceptance Criteria

- [ ] `uv sync` installs all dependencies
- [ ] `uv run llm-fmt --help` shows help text
- [ ] `uv build` creates distributable wheel
- [ ] `uvx --from . llm-fmt --help` works from project root

## Notes

- Using hatchling initially; will switch to maturin when adding Rust
- Consider adding `py.typed` marker for type checking support
- Entry point must match the function signature in cli.py
