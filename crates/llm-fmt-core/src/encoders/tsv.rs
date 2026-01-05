//! TSV (Tab-Separated Values) encoder.
//!
//! TSV is a token-efficient format for flat tabular data.
//! Tabs tokenize more efficiently than commas in most BPE vocabularies.

use crate::error::EncodeError;
use crate::value::{Number, Value};
use crate::Result;

use super::Encoder;

/// Encoder for TSV format.
///
/// Only supports uniform arrays of objects (flat tabular data).
#[derive(Debug, Default, Clone, Copy)]
pub struct TsvEncoder;

impl TsvEncoder {
    /// Create a new TSV encoder.
    #[must_use]
    pub const fn new() -> Self {
        Self
    }

    /// Encode a single value for a TSV cell.
    fn encode_value(&self, value: &Value) -> String {
        match value {
            Value::Null => String::new(),
            Value::Bool(b) => if *b { "true" } else { "false" }.to_string(),
            Value::Number(n) => self.encode_number(n),
            Value::String(s) => self.escape_tsv(s),
            Value::Array(arr) => self.escape_tsv(&format!("{arr:?}")),
            Value::Object(obj) => self.escape_tsv(&format!("{obj:?}")),
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

    /// Escape tabs and newlines in TSV values.
    fn escape_tsv(&self, value: &str) -> String {
        value
            .replace('\\', "\\\\")
            .replace('\t', "\\t")
            .replace('\n', "\\n")
            .replace('\r', "\\r")
    }
}

impl Encoder for TsvEncoder {
    fn encode(&self, value: &Value) -> Result<String> {
        let arr = value
            .as_array()
            .ok_or_else(|| EncodeError::Tsv("TSV format requires a list of objects".into()))?;

        if arr.is_empty() {
            return Ok(String::new());
        }

        // Get headers from first object
        let first = arr
            .first()
            .and_then(Value::as_object)
            .ok_or_else(|| EncodeError::Tsv("TSV format requires all items to be objects".into()))?;

        let headers: Vec<&String> = first.keys().collect();

        if headers.is_empty() {
            return Ok(String::new());
        }

        let mut lines = Vec::with_capacity(arr.len() + 1);

        // Header row
        lines.push(headers.iter().map(|h| h.as_str()).collect::<Vec<_>>().join("\t"));

        // Data rows
        for item in arr {
            let obj = item
                .as_object()
                .ok_or_else(|| EncodeError::Tsv("TSV format requires all items to be objects".into()))?;

            let values: Vec<String> = headers
                .iter()
                .map(|h| {
                    obj.get(*h)
                        .map(|v| self.encode_value(v))
                        .unwrap_or_default()
                })
                .collect();

            lines.push(values.join("\t"));
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
        let encoder = TsvEncoder::new();

        let mut obj1 = IndexMap::new();
        obj1.insert("name".to_string(), Value::from("Alice"));
        obj1.insert("age".to_string(), Value::from(30));

        let mut obj2 = IndexMap::new();
        obj2.insert("name".to_string(), Value::from("Bob"));
        obj2.insert("age".to_string(), Value::from(25));

        let arr = Value::Array(vec![Value::Object(obj1), Value::Object(obj2)]);
        let result = encoder.encode(&arr).unwrap();

        assert!(result.starts_with("name\tage"));
        assert!(result.contains("Alice\t30"));
        assert!(result.contains("Bob\t25"));
    }

    #[test]
    fn test_encode_with_nulls() {
        let encoder = TsvEncoder::new();

        let mut obj = IndexMap::new();
        obj.insert("name".to_string(), Value::from("test"));
        obj.insert("value".to_string(), Value::Null);

        let arr = Value::Array(vec![Value::Object(obj)]);
        let result = encoder.encode(&arr).unwrap();

        assert!(result.contains("name\tvalue"));
        assert!(result.contains("test\t"));
    }

    #[test]
    fn test_encode_escape_tabs() {
        let encoder = TsvEncoder::new();

        let mut obj = IndexMap::new();
        obj.insert("text".to_string(), Value::from("has\ttab"));

        let arr = Value::Array(vec![Value::Object(obj)]);
        let result = encoder.encode(&arr).unwrap();

        assert!(result.contains("has\\ttab"));
    }

    #[test]
    fn test_encode_escape_newlines() {
        let encoder = TsvEncoder::new();

        let mut obj = IndexMap::new();
        obj.insert("text".to_string(), Value::from("line1\nline2"));

        let arr = Value::Array(vec![Value::Object(obj)]);
        let result = encoder.encode(&arr).unwrap();

        assert!(result.contains("line1\\nline2"));
    }

    #[test]
    fn test_encode_empty() {
        let encoder = TsvEncoder::new();
        let arr = Value::Array(vec![]);
        let result = encoder.encode(&arr).unwrap();

        assert_eq!(result, "");
    }

    #[test]
    fn test_encode_non_array_error() {
        let encoder = TsvEncoder::new();
        let result = encoder.encode(&Value::from("not an array"));

        assert!(result.is_err());
    }
}
