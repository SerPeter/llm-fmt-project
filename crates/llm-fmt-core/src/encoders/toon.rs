//! TOON (Tabular Object-Oriented Notation) encoder.
//!
//! TOON is a token-efficient format for uniform arrays of objects.
//! It separates headers from data rows, achieving 30-60% token savings
//! compared to standard JSON.
//!
//! # Format
//!
//! ```text
//! @header:key1|key2|key3
//! value1|value2|value3
//! value4|value5|value6
//! ```
//!
//! For non-tabular data, TOON falls back to a compact notation:
//! - Objects: `{key1:value1,key2:value2}`
//! - Arrays: `[item1,item2,item3]`
//! - Strings with special chars: `"quoted string"`

use crate::error::EncodeError;
use crate::value::{Number, Value};
use crate::Result;

use super::Encoder;

/// Encoder for TOON format.
#[derive(Debug, Default, Clone)]
pub struct ToonEncoder {
    /// Pre-allocated buffer for encoding.
    buffer: String,
}

impl ToonEncoder {
    /// Create a new TOON encoder.
    #[must_use]
    pub fn new() -> Self {
        Self {
            buffer: String::with_capacity(4096),
        }
    }

    /// Encode to the internal buffer and return a reference.
    ///
    /// This is more efficient than `encode()` when encoding multiple values.
    ///
    /// # Errors
    ///
    /// Returns an error if encoding fails.
    pub fn encode_to(&mut self, value: &Value) -> Result<&str> {
        self.buffer.clear();
        self.write_value(value)?;
        Ok(&self.buffer)
    }

    /// Write a value to the buffer.
    fn write_value(&mut self, value: &Value) -> Result<()> {
        match value {
            Value::Null => self.buffer.push_str("null"),
            Value::Bool(b) => self.buffer.push_str(if *b { "true" } else { "false" }),
            Value::Number(n) => self.write_number(n),
            Value::String(s) => self.write_string(s),
            Value::Array(arr) => self.write_array(arr)?,
            Value::Object(obj) => self.write_object(obj)?,
        }
        Ok(())
    }

    /// Write a number to the buffer.
    fn write_number(&mut self, n: &Number) {
        match n {
            Number::Int(i) => self.buffer.push_str(&i.to_string()),
            Number::UInt(u) => self.buffer.push_str(&u.to_string()),
            Number::Float(f) => {
                // Use a compact representation
                if f.fract() == 0.0 && f.abs() < 1e15 {
                    self.buffer.push_str(&(*f as i64).to_string());
                } else {
                    self.buffer.push_str(&f.to_string());
                }
            }
        }
    }

    /// Write a string, quoting if necessary.
    fn write_string(&mut self, s: &str) {
        if Self::needs_quoting(s) {
            self.buffer.push('"');
            for c in s.chars() {
                match c {
                    '"' => self.buffer.push_str("\\\""),
                    '\\' => self.buffer.push_str("\\\\"),
                    '\n' => self.buffer.push_str("\\n"),
                    '\r' => self.buffer.push_str("\\r"),
                    '\t' => self.buffer.push_str("\\t"),
                    _ => self.buffer.push(c),
                }
            }
            self.buffer.push('"');
        } else {
            self.buffer.push_str(s);
        }
    }

    /// Check if a string needs quoting.
    fn needs_quoting(s: &str) -> bool {
        s.is_empty()
            || s.contains(|c: char| {
                matches!(
                    c,
                    '|' | ',' | ':' | '{' | '}' | '[' | ']' | '"' | '\n' | '\r' | '\t'
                )
            })
            || s.starts_with(char::is_whitespace)
            || s.ends_with(char::is_whitespace)
    }

    /// Write an array to the buffer.
    fn write_array(&mut self, arr: &[Value]) -> Result<()> {
        // Check if this is a uniform array of objects (tabular data)
        if let Some(headers) = Self::extract_uniform_headers(arr) {
            self.write_tabular(arr, &headers)?;
        } else {
            // Fallback to compact array notation
            self.buffer.push('[');
            for (i, item) in arr.iter().enumerate() {
                if i > 0 {
                    self.buffer.push(',');
                }
                self.write_value(item)?;
            }
            self.buffer.push(']');
        }
        Ok(())
    }

    /// Extract headers if all array elements are objects with the same keys.
    fn extract_uniform_headers(arr: &[Value]) -> Option<Vec<String>> {
        if arr.is_empty() {
            return None;
        }

        // Get headers from first object
        let first = arr.first()?.as_object()?;
        let headers: Vec<String> = first.keys().cloned().collect();

        if headers.is_empty() {
            return None;
        }

        // Check all other objects have the same keys
        for item in arr.iter().skip(1) {
            let obj = item.as_object()?;
            if obj.len() != headers.len() {
                return None;
            }
            for key in &headers {
                if !obj.contains_key(key) {
                    return None;
                }
            }
        }

        Some(headers)
    }

    /// Write tabular data with header row.
    fn write_tabular(&mut self, arr: &[Value], headers: &[String]) -> Result<()> {
        // Write header row
        self.buffer.push_str("@header:");
        for (i, header) in headers.iter().enumerate() {
            if i > 0 {
                self.buffer.push('|');
            }
            self.write_string(header);
        }
        self.buffer.push('\n');

        // Write data rows
        for item in arr {
            let obj = item
                .as_object()
                .ok_or_else(|| EncodeError::Toon("Expected object in tabular data".into()))?;

            for (i, header) in headers.iter().enumerate() {
                if i > 0 {
                    self.buffer.push('|');
                }
                if let Some(value) = obj.get(header) {
                    self.write_cell_value(value)?;
                }
            }
            self.buffer.push('\n');
        }

        Ok(())
    }

    /// Write a cell value (for tabular format).
    fn write_cell_value(&mut self, value: &Value) -> Result<()> {
        match value {
            Value::Null => {} // Empty cell for null
            Value::Bool(b) => self.buffer.push_str(if *b { "true" } else { "false" }),
            Value::Number(n) => self.write_number(n),
            Value::String(s) => self.write_string(s),
            Value::Array(_) | Value::Object(_) => {
                // Nested structures in cells use compact JSON-like notation
                self.write_value(value)?;
            }
        }
        Ok(())
    }

    /// Write an object to the buffer (compact notation).
    fn write_object(&mut self, obj: &indexmap::IndexMap<String, Value>) -> Result<()> {
        self.buffer.push('{');
        for (i, (key, value)) in obj.iter().enumerate() {
            if i > 0 {
                self.buffer.push(',');
            }
            self.write_string(key);
            self.buffer.push(':');
            self.write_value(value)?;
        }
        self.buffer.push('}');
        Ok(())
    }
}

impl Encoder for ToonEncoder {
    fn encode(&self, value: &Value) -> Result<String> {
        let mut encoder = Self::new();
        encoder.write_value(value)?;
        Ok(encoder.buffer)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use indexmap::IndexMap;

    #[test]
    fn test_encode_primitives() {
        let encoder = ToonEncoder::new();

        assert_eq!(encoder.encode(&Value::Null).unwrap(), "null");
        assert_eq!(encoder.encode(&Value::Bool(true)).unwrap(), "true");
        assert_eq!(encoder.encode(&Value::from(42)).unwrap(), "42");
        assert_eq!(encoder.encode(&Value::from("hello")).unwrap(), "hello");
    }

    #[test]
    fn test_encode_string_quoting() {
        let encoder = ToonEncoder::new();

        // No quoting needed
        assert_eq!(encoder.encode(&Value::from("simple")).unwrap(), "simple");

        // Needs quoting
        assert_eq!(
            encoder.encode(&Value::from("has|pipe")).unwrap(),
            r#""has|pipe""#
        );
        assert_eq!(
            encoder.encode(&Value::from("has\nnewline")).unwrap(),
            r#""has\nnewline""#
        );
    }

    #[test]
    fn test_encode_tabular_array() {
        let encoder = ToonEncoder::new();

        let mut obj1 = IndexMap::new();
        obj1.insert("name".to_string(), Value::from("Alice"));
        obj1.insert("age".to_string(), Value::from(30));

        let mut obj2 = IndexMap::new();
        obj2.insert("name".to_string(), Value::from("Bob"));
        obj2.insert("age".to_string(), Value::from(25));

        let arr = Value::Array(vec![Value::Object(obj1), Value::Object(obj2)]);
        let result = encoder.encode(&arr).unwrap();

        assert!(result.starts_with("@header:"));
        assert!(result.contains("name"));
        assert!(result.contains("age"));
        assert!(result.contains("Alice"));
        assert!(result.contains("Bob"));
    }

    #[test]
    fn test_encode_non_uniform_array() {
        let encoder = ToonEncoder::new();

        // Mixed types - should use compact notation
        let arr = Value::Array(vec![Value::from(1), Value::from("two"), Value::from(3)]);
        let result = encoder.encode(&arr).unwrap();

        assert_eq!(result, "[1,two,3]");
    }

    #[test]
    fn test_encode_nested_object() {
        let encoder = ToonEncoder::new();

        let mut inner = IndexMap::new();
        inner.insert("x".to_string(), Value::from(1));

        let mut outer = IndexMap::new();
        outer.insert("nested".to_string(), Value::Object(inner));

        let result = encoder.encode(&Value::Object(outer)).unwrap();
        assert_eq!(result, "{nested:{x:1}}");
    }
}
