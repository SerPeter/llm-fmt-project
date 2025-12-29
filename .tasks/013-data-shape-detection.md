# Task 013: Data Shape Detection

**Phase**: 3 - Auto-Selection & Polish  
**Priority**: +120
**Storypoints**: 5  
**Status**: [x] Complete

## Objective

Implement data structure analysis to inform format selection and provide insights.

## Requirements

- [x] Detect uniform vs non-uniform arrays
- [x] Calculate nesting depth
- [x] Identify field types and patterns
- [x] Sample large datasets efficiently
- [x] Provide shape summary for `--analyze`

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

- [x] Correctly identifies uniform arrays
- [x] Depth calculation is accurate
- [x] Large arrays sampled (not full scan)
- [x] Shape info available to auto-select
