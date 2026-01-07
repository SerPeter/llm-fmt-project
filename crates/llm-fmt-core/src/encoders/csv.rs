//! CSV (Comma-Separated Values) encoder.
//!
//! CSV is a widely-supported format for flat tabular data.

use crate::error::EncodeError;
use crate::value::{Number, Value};
use crate::Result;

use super::Encoder;

/// Encoder for CSV format.
///
/// Only supports uniform arrays of objects (flat tabular data).
#[derive(Debug, Default, Clone, Copy)]
pub struct CsvEncoder;

impl CsvEncoder {
    /// Create a new CSV encoder.
    #[must_use]
    pub const fn new() -> Self {
        Self
    }

    /// Encode a single value for a CSV cell.
    fn encode_value(&self, value: &Value) -> String {
        match value {
            Value::Null => String::new(),
            Value::Bool(b) => if *b { "true" } else { "false" }.to_string(),
            Value::Number(n) => self.encode_number(n),
            Value::String(s) => s.clone(),
            Value::Array(arr) => format!("{arr:?}"),
            Value::Object(obj) => format!("{obj:?}"),
        }
    }

    /// Encode a number.
    fn encode_number(&self, n: &Number) -> String {
        match n {
            Number::Int(i) => i.to_string(),
            Number::UInt(u) => u.to_string(),
            Number::Float(f) => f.to_string(),
        }
    }

    /// Escape and quote a CSV field if necessary.
    fn escape_csv(&self, value: &str) -> String {
        if value.contains(',')
            || value.contains('"')
            || value.contains('\n')
            || value.contains('\r')
        {
            let escaped = value.replace('"', "\"\"");
            format!("\"{escaped}\"")
        } else {
            value.to_string()
        }
    }
}

impl Encoder for CsvEncoder {
    fn encode(&self, value: &Value) -> Result<String> {
        let arr = value
            .as_array()
            .ok_or_else(|| EncodeError::Csv("CSV format requires a list of objects".into()))?;

        if arr.is_empty() {
            return Ok(String::new());
        }

        // Get headers from first object
        let first = arr.first().and_then(Value::as_object).ok_or_else(|| {
            EncodeError::Csv("CSV format requires all items to be objects".into())
        })?;

        let headers: Vec<&String> = first.keys().collect();

        if headers.is_empty() {
            return Ok(String::new());
        }

        let mut lines = Vec::with_capacity(arr.len() + 1);

        // Header row
        lines.push(
            headers
                .iter()
                .map(|h| self.escape_csv(h))
                .collect::<Vec<_>>()
                .join(","),
        );

        // Data rows
        for item in arr {
            let obj = item.as_object().ok_or_else(|| {
                EncodeError::Csv("CSV format requires all items to be objects".into())
            })?;

            let values: Vec<String> = headers
                .iter()
                .map(|h| {
                    let raw = obj
                        .get(*h)
                        .map(|v| self.encode_value(v))
                        .unwrap_or_default();
                    self.escape_csv(&raw)
                })
                .collect();

            lines.push(values.join(","));
        }

        Ok(lines.join("\n"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use indexmap::IndexMap;

    #[test]
    fn test_encode_simple() {
        let encoder = CsvEncoder::new();

        let mut obj1 = IndexMap::new();
        obj1.insert("name".to_string(), Value::from("Alice"));
        obj1.insert("age".to_string(), Value::from(30));

        let mut obj2 = IndexMap::new();
        obj2.insert("name".to_string(), Value::from("Bob"));
        obj2.insert("age".to_string(), Value::from(25));

        let arr = Value::Array(vec![Value::Object(obj1), Value::Object(obj2)]);
        let result = encoder.encode(&arr).unwrap();

        assert!(result.starts_with("name,age"));
        assert!(result.contains("Alice,30"));
        assert!(result.contains("Bob,25"));
    }

    #[test]
    fn test_encode_with_commas() {
        let encoder = CsvEncoder::new();

        let mut obj = IndexMap::new();
        obj.insert("text".to_string(), Value::from("has, comma"));

        let arr = Value::Array(vec![Value::Object(obj)]);
        let result = encoder.encode(&arr).unwrap();

        assert!(result.contains("\"has, comma\""));
    }

    #[test]
    fn test_encode_with_quotes() {
        let encoder = CsvEncoder::new();

        let mut obj = IndexMap::new();
        obj.insert("text".to_string(), Value::from("has \"quotes\""));

        let arr = Value::Array(vec![Value::Object(obj)]);
        let result = encoder.encode(&arr).unwrap();

        assert!(result.contains("\"has \"\"quotes\"\"\""));
    }

    #[test]
    fn test_encode_with_newlines() {
        let encoder = CsvEncoder::new();

        let mut obj = IndexMap::new();
        obj.insert("text".to_string(), Value::from("line1\nline2"));

        let arr = Value::Array(vec![Value::Object(obj)]);
        let result = encoder.encode(&arr).unwrap();

        assert!(result.contains("\"line1\nline2\""));
    }

    #[test]
    fn test_encode_empty() {
        let encoder = CsvEncoder::new();
        let arr = Value::Array(vec![]);
        let result = encoder.encode(&arr).unwrap();

        assert_eq!(result, "");
    }

    #[test]
    fn test_encode_non_array_error() {
        let encoder = CsvEncoder::new();
        let result = encoder.encode(&Value::from("not an array"));

        assert!(result.is_err());
    }
}
