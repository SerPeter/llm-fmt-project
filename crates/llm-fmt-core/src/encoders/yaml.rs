//! YAML encoder.
//!
//! Produces clean YAML output for human-readable, token-efficient format.

use crate::value::{Number, Value};
use crate::Result;

use super::Encoder;

/// Encoder for YAML format.
#[derive(Debug, Clone)]
pub struct YamlEncoder {
    /// Indentation width.
    indent: usize,
}

impl Default for YamlEncoder {
    fn default() -> Self {
        Self { indent: 2 }
    }
}

impl YamlEncoder {
    /// Create a new YAML encoder with default settings.
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Create a YAML encoder with custom indentation.
    #[must_use]
    pub const fn with_indent(indent: usize) -> Self {
        Self { indent }
    }

    /// Write value to buffer with given indentation level.
    fn write_value(&self, value: &Value, buffer: &mut String, level: usize, in_array: bool) {
        match value {
            Value::Null => buffer.push_str("null"),
            Value::Bool(b) => buffer.push_str(if *b { "true" } else { "false" }),
            Value::Number(n) => self.write_number(n, buffer),
            Value::String(s) => self.write_string(s, buffer),
            Value::Array(arr) => self.write_array(arr, buffer, level, in_array),
            Value::Object(obj) => self.write_object(obj, buffer, level, in_array),
        }
    }

    /// Write a number.
    fn write_number(&self, n: &Number, buffer: &mut String) {
        match n {
            Number::Int(i) => buffer.push_str(&i.to_string()),
            Number::UInt(u) => buffer.push_str(&u.to_string()),
            Number::Float(f) => {
                if f.is_finite() {
                    buffer.push_str(&f.to_string());
                } else {
                    buffer.push_str(".nan");
                }
            }
        }
    }

    /// Write a string, using literal block style for multiline.
    fn write_string(&self, s: &str, buffer: &mut String) {
        if s.is_empty() {
            buffer.push_str("''");
        } else if s.contains('\n') {
            // Use literal block style for multiline
            buffer.push_str("|\n");
            for line in s.lines() {
                buffer.push_str("  ");
                buffer.push_str(line);
                buffer.push('\n');
            }
        } else if self.needs_quoting(s) {
            // Quote strings with special characters
            buffer.push('"');
            for c in s.chars() {
                match c {
                    '"' => buffer.push_str("\\\""),
                    '\\' => buffer.push_str("\\\\"),
                    '\t' => buffer.push_str("\\t"),
                    '\r' => buffer.push_str("\\r"),
                    _ => buffer.push(c),
                }
            }
            buffer.push('"');
        } else {
            buffer.push_str(s);
        }
    }

    /// Check if a string needs quoting.
    fn needs_quoting(&self, s: &str) -> bool {
        if s.is_empty() {
            return true;
        }

        // Check for YAML special characters at start
        let first = s.chars().next().unwrap();
        if matches!(
            first,
            '-' | '?'
                | ':'
                | ','
                | '['
                | ']'
                | '{'
                | '}'
                | '#'
                | '&'
                | '*'
                | '!'
                | '|'
                | '>'
                | '\''
                | '"'
                | '%'
                | '@'
                | '`'
        ) {
            return true;
        }

        // Check for special values
        let lower = s.to_lowercase();
        if matches!(
            lower.as_str(),
            "true" | "false" | "null" | "yes" | "no" | "on" | "off"
        ) {
            return true;
        }

        // Check for colon followed by space
        if s.contains(": ") || s.ends_with(':') {
            return true;
        }

        // Check if it looks like a number
        if s.parse::<f64>().is_ok() {
            return true;
        }

        false
    }

    /// Write an array.
    fn write_array(&self, arr: &[Value], buffer: &mut String, level: usize, in_array: bool) {
        if arr.is_empty() {
            buffer.push_str("[]");
            return;
        }

        let indent = " ".repeat(self.indent * level);

        for (i, item) in arr.iter().enumerate() {
            if i > 0 || in_array {
                buffer.push('\n');
                buffer.push_str(&indent);
            }
            buffer.push_str("- ");

            match item {
                Value::Object(_) | Value::Array(_) => {
                    self.write_value(item, buffer, level + 1, true);
                }
                _ => {
                    self.write_value(item, buffer, level + 1, false);
                }
            }
        }
    }

    /// Write an object.
    fn write_object(
        &self,
        obj: &indexmap::IndexMap<String, Value>,
        buffer: &mut String,
        level: usize,
        in_array: bool,
    ) {
        if obj.is_empty() {
            buffer.push_str("{}");
            return;
        }

        let indent = " ".repeat(self.indent * level);

        for (i, (key, value)) in obj.iter().enumerate() {
            if i > 0 {
                buffer.push('\n');
                buffer.push_str(&indent);
            } else if in_array && !matches!(value, Value::Object(_) | Value::Array(_)) {
                // First key after array marker, no newline needed
            } else if in_array {
                buffer.push('\n');
                buffer.push_str(&indent);
            }

            // Write key
            if self.needs_quoting(key) {
                buffer.push('"');
                buffer.push_str(key);
                buffer.push('"');
            } else {
                buffer.push_str(key);
            }
            buffer.push(':');

            match value {
                Value::Object(_) | Value::Array(_) => {
                    self.write_value(value, buffer, level + 1, false);
                }
                _ => {
                    buffer.push(' ');
                    self.write_value(value, buffer, level + 1, false);
                }
            }
        }
    }
}

impl Encoder for YamlEncoder {
    fn encode(&self, value: &Value) -> Result<String> {
        let mut buffer = String::with_capacity(256);
        self.write_value(value, &mut buffer, 0, false);
        buffer.push('\n');
        Ok(buffer)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use indexmap::IndexMap;

    #[test]
    fn test_encode_primitives() {
        let encoder = YamlEncoder::new();

        assert_eq!(encoder.encode(&Value::Null).unwrap(), "null\n");
        assert_eq!(encoder.encode(&Value::Bool(true)).unwrap(), "true\n");
        assert_eq!(encoder.encode(&Value::from(42)).unwrap(), "42\n");
    }

    #[test]
    fn test_encode_string() {
        let encoder = YamlEncoder::new();

        assert_eq!(encoder.encode(&Value::from("hello")).unwrap(), "hello\n");
        assert_eq!(encoder.encode(&Value::from("true")).unwrap(), "\"true\"\n");
    }

    #[test]
    fn test_encode_array() {
        let encoder = YamlEncoder::new();
        let arr = Value::Array(vec![Value::from(1), Value::from(2), Value::from(3)]);
        let result = encoder.encode(&arr).unwrap();

        assert!(result.contains("- 1"));
        assert!(result.contains("- 2"));
        assert!(result.contains("- 3"));
    }

    #[test]
    fn test_encode_object() {
        let encoder = YamlEncoder::new();
        let mut obj = IndexMap::new();
        obj.insert("name".to_string(), Value::from("Alice"));
        obj.insert("age".to_string(), Value::from(30));
        let result = encoder.encode(&Value::Object(obj)).unwrap();

        assert!(result.contains("name: Alice"));
        assert!(result.contains("age: 30"));
    }

    #[test]
    fn test_encode_nested() {
        let encoder = YamlEncoder::new();
        let mut inner = IndexMap::new();
        inner.insert("id".to_string(), Value::from(1));

        let mut outer = IndexMap::new();
        outer.insert("user".to_string(), Value::Object(inner));

        let result = encoder.encode(&Value::Object(outer)).unwrap();
        assert!(result.contains("user:"));
        assert!(result.contains("id: 1"));
    }
}
