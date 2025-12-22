# Task 017: Configuration File Support

**Phase**: 3 - Auto-Selection & Polish  
**Priority**: +40
**Storypoints**: 3  
**Status**: [ ] Not started

## Objective

Support configuration files for default settings.

## Requirements

- [ ] Read `.llm-fmt.toml` from current dir or home
- [ ] Default format, tokenizer, exclusions
- [ ] Override with CLI flags
- [ ] `--config` to specify custom path

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

- [ ] Config file discovered automatically
- [ ] CLI flags override config
- [ ] Missing config is okay (use defaults)
- [ ] Invalid config shows clear error
