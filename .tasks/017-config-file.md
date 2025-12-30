# Task 017: Configuration File Support

**Phase**: 3 - Auto-Selection & Polish
**Priority**: +40
**Storypoints**: 3
**Status**: [x] Complete

## Objective

Support configuration files for default settings.

## Requirements

- [x] Read `.llm-fmt.toml` from current dir or home
- [x] Default format, tokenizer, exclusions
- [x] Override with CLI flags
- [x] `--config` to specify custom path

## Configuration Format

```toml
# .llm-fmt.toml
[defaults]
format = "auto"
tokenizer = "cl100k_base"

[filter]
default_exclude = ["_metadata", "_links", "debug"]
default_max_depth = 5

[output]
color = true
```

## Acceptance Criteria

- [x] Config file discovered automatically
- [x] CLI flags override config
- [x] Missing config is okay (use defaults)
- [x] Invalid config shows clear error
