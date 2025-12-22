# Task 019: PyPI Packaging & Release

**Phase**: 3 - Auto-Selection & Polish  
**Priority**: +200
**Storypoints**: 3  
**Status**: [ ] Not started

## Objective

Package and publish to PyPI for installation via pip/uvx.

## Requirements

- [ ] Build distributable wheel and sdist
- [ ] Publish to TestPyPI first
- [ ] Publish to PyPI
- [ ] Verify `uvx llm-fmt` works globally
- [ ] Set up GitHub Actions for automated releases

## Pre-Release Checklist

- [ ] All tests passing
- [ ] README renders correctly on PyPI
- [ ] Version number set (e.g., 0.1.0)
- [ ] CHANGELOG updated
- [ ] License file present
- [ ] Author/contact info correct

## Build Process

```bash
# Ensure build tools installed
uv add --dev build twine

# Build wheel and sdist
uv run python -m build

# Check distribution
uv run twine check dist/*

# Test install locally
uv venv test-env
source test-env/bin/activate
pip install dist/llm_fmt-0.1.0-py3-none-any.whl
llm-fmt --version
```

## Publishing

### TestPyPI (First)

```bash
# Upload to TestPyPI
uv run twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ llm-fmt
```

### PyPI (Production)

```bash
# Upload to PyPI
uv run twine upload dist/*

# Verify installation
pip install llm-fmt
uvx llm-fmt --help
```

## GitHub Actions Workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # For trusted publishing
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Install dependencies
        run: uv sync --all-extras
      
      - name: Run tests
        run: uv run pytest
      
      - name: Build package
        run: uv run python -m build
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # Uses trusted publishing - no token needed
```

### Trusted Publishing Setup

1. Go to PyPI → Account → Publishing
2. Add new publisher:
   - Owner: your-github-username
   - Repository: llm-fmt
   - Workflow: release.yml
   - Environment: (leave blank)

## Version Management

Using dynamic versioning from git tags:

```toml
# pyproject.toml
[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.hooks.vcs]
version-file = "src/llm_fmt/_version.py"
```

Or manual versioning:

```toml
[project]
version = "0.1.0"
```

## Release Process

1. Update CHANGELOG.md
2. Commit: `git commit -am "Prepare release v0.1.0"`
3. Tag: `git tag v0.1.0`
4. Push: `git push origin main --tags`
5. GitHub Actions builds and publishes

## Verification

```bash
# Fresh environment test
python -m venv /tmp/test-llm-fmt
source /tmp/test-llm-fmt/bin/activate
pip install llm-fmt
llm-fmt --version
echo '{"test": 1}' | llm-fmt -f toon

# uvx test
uvx llm-fmt --help
echo '{"a": 1}' | uvx llm-fmt -f compact-json
```

## PyPI Metadata

Ensure pyproject.toml has:

```toml
[project]
name = "llm-fmt"
description = "Token-efficient data format converter for LLM contexts"
readme = "README.md"
license = { text = "MIT" }
keywords = ["llm", "tokens", "json", "toon", "ai", "agents", "gpt", "claude"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries",
    "Topic :: Text Processing",
    "Typing :: Typed",
]

[project.urls]
Homepage = "https://github.com/youruser/llm-fmt"
Documentation = "https://github.com/youruser/llm-fmt#readme"
Repository = "https://github.com/youruser/llm-fmt"
Issues = "https://github.com/youruser/llm-fmt/issues"
Changelog = "https://github.com/youruser/llm-fmt/blob/main/CHANGELOG.md"
```

## Acceptance Criteria

- [ ] `pip install llm-fmt` works from PyPI
- [ ] `uvx llm-fmt` works without prior install
- [ ] Package metadata displays correctly on PyPI
- [ ] README renders properly
- [ ] GitHub Actions workflow automated

## Notes

- First release: use 0.1.0 (alpha/beta)
- Follow semver for subsequent releases
- Consider using `uv publish` (newer, simpler) when stable
- Trusted publishing avoids API token management
