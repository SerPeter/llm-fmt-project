# Task 013: Data Shape Detection

**Phase**: 3 - Auto-Selection & Polish  
**Priority**: +120
**Storypoints**: 5  
**Status**: [ ] Not started

## Objective

Implement data structure analysis to inform format selection and provide insights.

## Requirements

- [ ] Detect uniform vs non-uniform arrays
- [ ] Calculate nesting depth
- [ ] Identify field types and patterns
- [ ] Sample large datasets efficiently
- [ ] Provide shape summary for `--analyze`

## Implementation

See [Task 014](014-auto-format.md) for `DataShape` dataclass and detection logic.

## Key Metrics to Detect

- Root type (object, array, primitive)
- Array uniformity (same keys across items)
- Maximum nesting depth
- Primitive vs complex value ratio
- Array lengths at each level
- Common field names

## Acceptance Criteria

- [ ] Correctly identifies uniform arrays
- [ ] Depth calculation is accurate
- [ ] Large arrays sampled (not full scan)
- [ ] Shape info available to auto-select
