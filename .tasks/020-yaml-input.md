# Task 020: YAML Input Support

**Phase**: 4 - Extended Formats
**Priority**: -50
**Storypoints**: 2
**Status**: [x] Complete

## Objective

Add support for YAML as an input format, allowing YAML files to be converted to any output format.

## Requirements

- [x] Parse YAML input files
- [x] Auto-detect YAML from .yaml/.yml extension
- [x] Support --input-format yaml option
- [x] Handle YAML-specific features (anchors, aliases)
- [x] Convert YAML to all output formats

## Implementation

```python
class YamlParser:
    """Parser for YAML input data."""

    def parse(self, data: bytes) -> Any:
        """Parse YAML bytes into Python object."""
        return yaml.safe_load(data)
```

## CLI Usage

```bash
# Auto-detect from extension
llm-fmt config.yaml -f json

# Explicit input format
llm-fmt data.txt --input-format yaml -f toon

# Pipe YAML to TOON
cat config.yaml | llm-fmt -F yaml -f toon
```

## Acceptance Criteria

- [x] YamlParser parses valid YAML
- [x] Auto-detection works for .yaml and .yml files
- [x] --input-format yaml overrides auto-detection
- [x] All output formats work with YAML input
