//! YAML parser implementation.

use crate::error::ParseError;
use crate::value::{Number, Value};
use crate::Result;

use super::Parser;

/// Parser for YAML input.
#[derive(Debug, Default, Clone, Copy)]
pub struct YamlParser;

impl Parser for YamlParser {
    fn parse(&self, input: &[u8]) -> Result<Value> {
        let yaml_value: serde_yaml::Value =
            serde_yaml::from_slice(input).map_err(ParseError::from)?;
        Ok(convert_yaml_value(yaml_value))
    }
}

/// Convert a `serde_yaml::Value` to our internal `Value` type.
fn convert_yaml_value(value: serde_yaml::Value) -> Value {
    match value {
        serde_yaml::Value::Null => Value::Null,
        serde_yaml::Value::Bool(b) => Value::Bool(b),
        serde_yaml::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Value::Number(Number::Int(i))
            } else if let Some(u) = n.as_u64() {
                Value::Number(Number::UInt(u))
            } else if let Some(f) = n.as_f64() {
                Value::Number(Number::Float(f))
            } else {
                Value::Number(Number::Float(0.0))
            }
        }
        serde_yaml::Value::String(s) => Value::String(s),
        serde_yaml::Value::Sequence(seq) => {
            Value::Array(seq.into_iter().map(convert_yaml_value).collect())
        }
        serde_yaml::Value::Mapping(map) => {
            let obj = map
                .into_iter()
                .filter_map(|(k, v)| {
                    // Convert key to string
                    let key = match k {
                        serde_yaml::Value::String(s) => s,
                        serde_yaml::Value::Number(n) => n.to_string(),
                        serde_yaml::Value::Bool(b) => b.to_string(),
                        _ => return None,
                    };
                    Some((key, convert_yaml_value(v)))
                })
                .collect();
            Value::Object(obj)
        }
        serde_yaml::Value::Tagged(tagged) => convert_yaml_value(tagged.value),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple_object() {
        let parser = YamlParser;
        let input = b"name: Alice\nage: 30";
        let result = parser.parse(input).unwrap();

        assert!(result.is_object());
        assert_eq!(result.get("name").and_then(Value::as_str), Some("Alice"));
        assert_eq!(
            result.get("age").and_then(|v| v.as_number()?.as_i64()),
            Some(30)
        );
    }

    #[test]
    fn test_parse_array() {
        let parser = YamlParser;
        let input = b"- 1\n- 2\n- 3\n- 4\n- 5";
        let result = parser.parse(input).unwrap();

        assert!(result.is_array());
        let arr = result.as_array().unwrap();
        assert_eq!(arr.len(), 5);
    }

    #[test]
    fn test_parse_nested() {
        let parser = YamlParser;
        let input = b"users:\n  - id: 1\n  - id: 2";
        let result = parser.parse(input).unwrap();

        let users = result.get("users").and_then(Value::as_array).unwrap();
        assert_eq!(users.len(), 2);
    }

    #[test]
    fn test_parse_multiline_string() {
        let parser = YamlParser;
        let input = b"text: |\n  line1\n  line2";
        let result = parser.parse(input).unwrap();

        let text = result.get("text").and_then(Value::as_str).unwrap();
        assert!(text.contains("line1"));
        assert!(text.contains("line2"));
    }
}
