# Task 005: YAML Output Format

**Phase**: 1 - MVP  
**Priority**: +100
**Storypoints**: 3  
**Status**: [ ] Not started

## Objective

Implement YAML output as a token-efficient alternative for key-value heavy data.

## Requirements

- [ ] Output valid YAML 1.2
- [ ] Use block style (not flow style) for readability
- [ ] Minimal quoting (only when necessary)
- [ ] Configure indent width
- [ ] Handle multi-line strings cleanly

## Implementation Details

```python
# src/llm_fmt/formats/yaml_fmt.py
from typing import Any
import yaml


class CleanYamlDumper(yaml.SafeDumper):
    """Custom dumper that produces clean, minimal YAML."""
    pass


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    """Use literal block style for multi-line strings."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


CleanYamlDumper.add_representer(str, _str_representer)


def encode_yaml(
    data: Any,
    indent: int = 2,
    default_flow_style: bool = False,
) -> str:
    """
    Encode data to clean YAML.
    
    Args:
        data: Any YAML-serializable data
        indent: Indentation width
        default_flow_style: Use compact flow style for small structures
        
    Returns:
        YAML string
    """
    return yaml.dump(
        data,
        Dumper=CleanYamlDumper,
        default_flow_style=default_flow_style,
        indent=indent,
        allow_unicode=True,
        sort_keys=False,
        width=1000,  # Prevent line wrapping
    )
```

### Output Example

**JSON input:**
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "credentials": {
      "user": "admin",
      "password": "secret"
    }
  },
  "features": ["auth", "logging", "metrics"]
}
```

**YAML output:**
```yaml
database:
  host: localhost
  port: 5432
  credentials:
    user: admin
    password: secret
features:
  - auth
  - logging
  - metrics
```

## Token Efficiency

YAML saves tokens by eliminating:
- Braces `{}` and brackets `[]`
- Quotes around most strings
- Commas between elements

Typical savings: **20-40%** vs JSON for config-style data.

## Acceptance Criteria

- [ ] Valid YAML output parseable by any YAML parser
- [ ] Multi-line strings use literal block style (`|`)
- [ ] Numbers and booleans unquoted
- [ ] Unicode characters preserved
- [ ] No unnecessary quotes on simple strings

## Test Cases

```python
def test_basic_yaml():
    data = {"name": "test", "count": 42}
    result = encode_yaml(data)
    assert "name: test" in result
    assert "count: 42" in result

def test_multiline_string():
    data = {"content": "line1\nline2\nline3"}
    result = encode_yaml(data)
    assert "content: |" in result

def test_nested():
    ...
```

## Dependencies

- `pyyaml>=6.0`

## Notes

- PyYAML's CSafeLoader/CSafeDumper use C extension for speed
- Flow style (`{a: 1, b: 2}`) is more compact but less readable
- Consider ruamel.yaml for better YAML 1.2 support if needed
- YAML is especially good for configs where humans might also read
