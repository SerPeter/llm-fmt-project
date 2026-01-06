# Task 016: Error Handling & Validation

**Phase**: 3 - Auto-Selection & Polish
**Priority**: -100
**Storypoints**: 3
**Status**: [x] Complete

## Objective

Implement comprehensive error handling with helpful messages.

## Requirements

- [x] Clear error messages for all failure modes
- [x] Exit codes: 0 (success), 1 (error), 2 (invalid input)
- [x] Validate filter patterns before applying
- [x] Handle encoding issues gracefully
- [x] Log warnings for non-fatal issues

## Error Categories

1. **Input errors**: File not found, invalid JSON, encoding issues
2. **Filter errors**: Invalid dpath pattern, no matches
3. **Format errors**: Data incompatible with format (e.g., TSV on nested)
4. **Output errors**: Cannot write file, permission denied

## Implementation

```python
class LLMFmtError(Exception):
    """Base exception for llm-fmt."""
    exit_code = 1

class InputError(LLMFmtError):
    """Input file or parsing error."""
    exit_code = 2

class FilterError(LLMFmtError):
    """Invalid filter pattern."""
    pass

class FormatError(LLMFmtError):
    """Data incompatible with requested format."""
    pass
```

## Acceptance Criteria

- [x] All errors show helpful messages
- [x] Exit codes are consistent
- [x] No stack traces in normal use
- [x] `--debug` flag shows full traceback
