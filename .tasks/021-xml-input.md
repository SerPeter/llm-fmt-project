# Task 021: XML Input Support

**Phase**: 4 - Extended Formats
**Priority**: -50
**Storypoints**: 3
**Status**: [x] Complete

## Objective

Add support for XML as an input format, allowing XML files to be converted to any output format.

## Requirements

- [x] Parse XML input using xmltodict
- [x] Auto-detect XML from .xml extension
- [x] Auto-detect XML from content (<?xml or <root>)
- [x] Support --input-format xml option
- [x] Handle attributes as @-prefixed keys
- [x] Handle repeating elements as arrays
- [x] Support CDATA sections

## Implementation

```python
class XmlParser:
    """Parser for XML input data."""

    def __init__(self, *, strip_namespace: bool = True) -> None:
        self.strip_namespace = strip_namespace

    def parse(self, data: bytes) -> Any:
        text = data.decode("utf-8")
        return xmltodict.parse(text)
```

## CLI Usage

```bash
# Auto-detect from extension
llm-fmt data.xml -f json

# Auto-detect from content
cat data.xml | llm-fmt -f yaml

# Explicit input format
llm-fmt data.txt --input-format xml -f toon
```

## XML to JSON Mapping

| XML Feature | JSON Representation |
|-------------|---------------------|
| Element | Object key |
| Attribute | @-prefixed key |
| Text content | #text key |
| Repeated elements | Array |
| CDATA | String value |

## Acceptance Criteria

- [x] XmlParser parses valid XML
- [x] Auto-detection works for .xml files
- [x] Auto-detection works from content (<?xml, <)
- [x] Attributes map to @-prefixed keys
- [x] Repeated elements become arrays
- [x] CDATA sections are preserved
- [x] All output formats work with XML input
