# Task 017: Configuration File Support

**Phase**: 3 - Auto-Selection & Polish
**Priority**: +40
**Storypoints**: 5
**Status**: [x] Complete

## Objective

Implement a robust configuration system with hierarchical precedence, strong defaults, and multiple config file formats. The system should prevent accidental context window flooding while remaining flexible.

## Configuration Hierarchy (highest to lowest priority)

1. **CLI arguments** - Always override everything
2. **Environment variables** - `LLM_FMT_*` prefix
3. **Dedicated config file** - `.llm-fmt.yaml` / `.llm-fmt.toml`
4. **pyproject.toml** - `[tool.llm-fmt]` section
5. **Strong defaults** - Safe out-of-box behavior

## Strong Defaults

These defaults are designed to prevent accidentally consuming entire LLM context windows while still being useful. The max_tokens default of 10,000 represents ~10% of a 100K context window, leaving room for system prompts, conversation history, and model responses.

```yaml
defaults:
  format: auto              # Auto-select best format based on data shape
  input_format: auto        # Auto-detect input format

limits:
  max_tokens: 10000         # Hard cap on output tokens (~10% of 100K context)
  max_items: 500            # Prevent huge arrays from flooding context
  max_string_length: 500    # Truncate long string values
  max_depth: 8              # Reasonable nesting limit

truncation:
  strategy: head            # Keep first N items (head/tail/sample/balanced)
  show_summary: true        # Append "[...N more items]" when truncating

filter:
  default_exclude: []       # No global exclusions by default

output:
  strict: false             # If true, error instead of truncating
```

## Config File Search Path

Search in order, stop at first found:

1. `./.llm-fmt.yaml` (or `.yml`)
2. `./.llm-fmt.toml`
3. `./pyproject.toml` (check for `[tool.llm-fmt]`)
4. Walk up parent directories (stop at `.git` or filesystem root)
5. `~/.config/llm-fmt/config.yaml` (user-level default)

## Environment Variables

All config options can be set via environment variables with `LLM_FMT_` prefix:

```bash
LLM_FMT_FORMAT=toon
LLM_FMT_MAX_TOKENS=5000
LLM_FMT_MAX_ITEMS=100
LLM_FMT_MAX_DEPTH=5
LLM_FMT_STRICT=true
LLM_FMT_DEFAULT_EXCLUDE=_metadata,_links,debug
```

Boolean values: `true`, `false`, `1`, `0`, `yes`, `no`
List values: Comma-separated

## Config File Formats

### `.llm-fmt.yaml` (preferred)

```yaml
# .llm-fmt.yaml
defaults:
  format: toon
  input_format: auto

limits:
  max_tokens: 8000
  max_items: 200
  max_string_length: 300
  max_depth: 6

truncation:
  strategy: balanced
  show_summary: true

filter:
  default_exclude:
    - _metadata
    - _links
    - debug
    - internal
    - __v

output:
  strict: false
```

### `.llm-fmt.toml`

```toml
# .llm-fmt.toml

[defaults]
format = "toon"
input_format = "auto"

[limits]
max_tokens = 8000
max_items = 200
max_string_length = 300
max_depth = 6

[truncation]
strategy = "balanced"
show_summary = true

[filter]
default_exclude = ["_metadata", "_links", "debug"]

[output]
strict = false
```

### `pyproject.toml`

```toml
[tool.llm-fmt]
format = "toon"
max_tokens = 8000
max_items = 200

[tool.llm-fmt.filter]
default_exclude = ["_metadata", "_links"]

[tool.llm-fmt.truncation]
strategy = "balanced"
```

## CLI Options

New/updated CLI options:

```
--config PATH          Explicit config file path (skip search)
--no-config            Ignore all config files, use defaults only
--strict               Error instead of truncating (overrides config)
--no-strict            Allow truncation (overrides config)
--max-tokens N         Maximum output tokens (overrides config)
--show-config          Print resolved configuration and exit
```

## Strict Mode

When `strict: true` (or `--strict`):
- If output would exceed `max_tokens`, raise an error instead of truncating
- If array has more items than `max_items`, raise an error
- If string exceeds `max_string_length`, raise an error
- Useful for CI/validation where silent truncation could hide issues

Error message example:
```
Error: Output exceeds max_tokens limit (15,234 > 10,000 tokens)
Hint: Use --max-tokens to increase limit, or remove --strict to allow truncation
```

## Implementation

### Python Module: `src/llm_fmt/config.py`

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import os
import tomllib
import yaml

@dataclass
class LimitsConfig:
    max_tokens: int = 10000
    max_items: int = 500
    max_string_length: int = 500
    max_depth: int = 8

@dataclass
class TruncationConfig:
    strategy: str = "head"
    show_summary: bool = True

@dataclass
class FilterConfig:
    default_exclude: list[str] = field(default_factory=list)

@dataclass
class OutputConfig:
    strict: bool = False

@dataclass
class Config:
    format: str = "auto"
    input_format: str = "auto"
    limits: LimitsConfig = field(default_factory=LimitsConfig)
    truncation: TruncationConfig = field(default_factory=TruncationConfig)
    filter: FilterConfig = field(default_factory=FilterConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def load(cls, config_path: Path | None = None, no_config: bool = False) -> "Config":
        """Load config with full hierarchy resolution."""
        config = cls()  # Start with defaults

        if not no_config:
            # Find and load config file
            if config_path:
                config = cls._merge(config, cls._load_file(config_path))
            else:
                config = cls._merge(config, cls._find_and_load())

        # Apply environment variables (higher priority)
        config = cls._apply_env(config)

        return config

    @classmethod
    def _find_and_load(cls) -> dict[str, Any]:
        """Search for config files in standard locations."""
        # Implementation: walk up directories, check each location
        ...

def load_config(
    config_path: Path | None = None,
    no_config: bool = False,
    cli_overrides: dict[str, Any] | None = None,
) -> Config:
    """Main entry point for config loading."""
    config = Config.load(config_path, no_config)

    if cli_overrides:
        # Apply CLI arguments (highest priority)
        config = _apply_cli_overrides(config, cli_overrides)

    return config
```

### Integration with CLI

```python
@click.command()
@click.option("--config", "config_path", type=click.Path(exists=True))
@click.option("--no-config", is_flag=True)
@click.option("--strict", is_flag=True, default=None)
@click.option("--max-tokens", type=int, default=None)
# ... other options ...
def main(config_path, no_config, strict, max_tokens, ...):
    # Load config with hierarchy
    config = load_config(
        config_path=config_path,
        no_config=no_config,
        cli_overrides={
            "output.strict": strict,
            "limits.max_tokens": max_tokens,
            # ... only include non-None values
        }
    )

    # Use resolved config
    result = rust_convert(
        data,
        format=config.format,
        max_depth=config.limits.max_depth,
        max_items=config.limits.max_items,
        # ...
    )
```

## Acceptance Criteria

- [x] Strong defaults applied when no config found
- [x] `.llm-fmt.yaml` loaded from current/parent directories
- [x] `.llm-fmt.toml` loaded as alternative format
- [x] `pyproject.toml` `[tool.llm-fmt]` section supported
- [x] `~/.config/llm-fmt/config.yaml` user-level config supported
- [x] Environment variables (`LLM_FMT_*`) override file config
- [x] CLI arguments override everything
- [x] `--config PATH` skips search and uses explicit file
- [x] `--no-config` ignores all config files
- [x] `--strict` mode errors instead of truncating
- [x] `--show-config` prints resolved configuration
- [ ] Invalid config shows clear error with file path and line number
- [x] Missing config files are silently ignored (use defaults)
- [x] max_tokens limit enforced with clear error in strict mode

## Test Cases

```python
def test_defaults_when_no_config():
    config = load_config(no_config=True)
    assert config.limits.max_tokens == 10000
    assert config.limits.max_items == 500
    assert config.format == "auto"

def test_yaml_config_loaded():
    # Create temp .llm-fmt.yaml
    config = load_config()
    assert config.limits.max_tokens == 8000  # from file

def test_env_overrides_file():
    os.environ["LLM_FMT_MAX_TOKENS"] = "5000"
    config = load_config()
    assert config.limits.max_tokens == 5000

def test_cli_overrides_env():
    os.environ["LLM_FMT_MAX_TOKENS"] = "5000"
    config = load_config(cli_overrides={"limits.max_tokens": 3000})
    assert config.limits.max_tokens == 3000

def test_strict_mode_errors():
    config = load_config(cli_overrides={"output.strict": True})
    with pytest.raises(TokenLimitExceededError):
        convert(huge_data, config=config)

def test_pyproject_toml_loaded():
    # Config under [tool.llm-fmt]
    config = load_config()
    assert config.format == "toon"  # from pyproject.toml
```

## Dependencies

- `pyyaml` - YAML parsing (already a dependency)
- `tomllib` - TOML parsing (stdlib in Python 3.11+)

## Notes

- Config loading happens once at CLI startup, not per-conversion
- Rust core receives resolved values, doesn't know about config files
- Consider caching config for repeated calls in library usage
- Future: `llm-fmt config init` command to generate default config file
