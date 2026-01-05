//! JSON parser implementation.

use crate::error::ParseError;
use crate::value::{Number, Value};
use crate::Result;

use super::Parser;

/// Parser for JSON input.
#[derive(Debug, Default, Clone, Copy)]
pub struct JsonParser;

impl Parser for JsonParser {
    fn parse(&self, input: &[u8]) -> Result<Value> {
        let json_value: serde_json::Value =
            serde_json::from_slice(input).map_err(ParseError::from)?;
        Ok(convert_json_value(json_value))
    }
}

/// Convert a `serde_json::Value` to our internal `Value` type.
fn convert_json_value(value: serde_json::Value) -> Value {
    match value {
        serde_json::Value::Null => Value::Null,
        serde_json::Value::Bool(b) => Value::Bool(b),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Value::Number(Number::Int(i))
            } else if let Some(u) = n.as_u64() {
                Value::Number(Number::UInt(u))
            } else if let Some(f) = n.as_f64() {
                Value::Number(Number::Float(f))
            } else {
                // Fallback - should not happen with valid JSON
                Value::Number(Number::Float(0.0))
            }
        }
        serde_json::Value::String(s) => Value::String(s),
        serde_json::Value::Array(arr) => {
            Value::Array(arr.into_iter().map(convert_json_value).collect())
        }
        serde_json::Value::Object(obj) => {
            Value::Object(obj.into_iter().map(|(k, v)| (k, convert_json_value(v))).collect())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple_object() {
        let parser = JsonParser;
        let input = br#"{"name": "Alice", "age": 30}"#;
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
        let parser = JsonParser;
        let input = br#"[1, 2, 3, 4, 5]"#;
        let result = parser.parse(input).unwrap();

        assert!(result.is_array());
        let arr = result.as_array().unwrap();
        assert_eq!(arr.len(), 5);
    }

    #[test]
    fn test_parse_nested() {
        let parser = JsonParser;
        let input = br#"{"users": [{"id": 1}, {"id": 2}]}"#;
        let result = parser.parse(input).unwrap();

        let users = result.get("users").and_then(Value::as_array).unwrap();
        assert_eq!(users.len(), 2);
    }

    #[test]
    fn test_parse_invalid_json() {
        let parser = JsonParser;
        let input = b"not valid json";
        assert!(parser.parse(input).is_err());
    }
}
