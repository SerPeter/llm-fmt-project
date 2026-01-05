//! Compact JSON encoder.
//!
//! Encodes values to minified JSON with optional key sorting.

use crate::value::{Number, Value};
use crate::Result;

use super::Encoder;

/// Encoder for compact JSON format.
#[derive(Debug, Default, Clone)]
pub struct JsonEncoder {
    /// Whether to sort object keys alphabetically.
    sort_keys: bool,
    /// Pre-allocated buffer for encoding.
    buffer: String,
}

impl JsonEncoder {
    /// Create a new JSON encoder.
    #[must_use]
    pub const fn new(sort_keys: bool) -> Self {
        Self {
            sort_keys,
            buffer: String::new(),
        }
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
                if f.is_finite() {
                    self.buffer.push_str(&f.to_string());
                } else {
                    self.buffer.push_str("null"); // JSON doesn't support Infinity/NaN
                }
            }
        }
    }

    /// Write a JSON-escaped string.
    fn write_string(&mut self, s: &str) {
        self.buffer.push('"');
        for c in s.chars() {
            match c {
                '"' => self.buffer.push_str("\\\""),
                '\\' => self.buffer.push_str("\\\\"),
                '\n' => self.buffer.push_str("\\n"),
                '\r' => self.buffer.push_str("\\r"),
                '\t' => self.buffer.push_str("\\t"),
                c if c.is_control() => {
                    self.buffer.push_str(&format!("\\u{:04x}", c as u32));
                }
                _ => self.buffer.push(c),
            }
        }
        self.buffer.push('"');
    }

    /// Write an array to the buffer.
    fn write_array(&mut self, arr: &[Value]) -> Result<()> {
        self.buffer.push('[');
        for (i, item) in arr.iter().enumerate() {
            if i > 0 {
                self.buffer.push(',');
            }
            self.write_value(item)?;
        }
        self.buffer.push(']');
        Ok(())
    }

    /// Write an object to the buffer.
    fn write_object(&mut self, obj: &indexmap::IndexMap<String, Value>) -> Result<()> {
        self.buffer.push('{');

        if self.sort_keys {
            // Sort keys alphabetically
            let mut keys: Vec<_> = obj.keys().collect();
            keys.sort();

            for (i, key) in keys.iter().enumerate() {
                if i > 0 {
                    self.buffer.push(',');
                }
                self.write_string(key);
                self.buffer.push(':');
                if let Some(value) = obj.get(*key) {
                    self.write_value(value)?;
                }
            }
        } else {
            // Preserve insertion order
            for (i, (key, value)) in obj.iter().enumerate() {
                if i > 0 {
                    self.buffer.push(',');
                }
                self.write_string(key);
                self.buffer.push(':');
                self.write_value(value)?;
            }
        }

        self.buffer.push('}');
        Ok(())
    }
}

impl Encoder for JsonEncoder {
    fn encode(&self, value: &Value) -> Result<String> {
        let mut encoder = Self::new(self.sort_keys);
        encoder.buffer.reserve(256);
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
        let encoder = JsonEncoder::new(false);

        assert_eq!(encoder.encode(&Value::Null).unwrap(), "null");
        assert_eq!(encoder.encode(&Value::Bool(true)).unwrap(), "true");
        assert_eq!(encoder.encode(&Value::Bool(false)).unwrap(), "false");
        assert_eq!(encoder.encode(&Value::from(42)).unwrap(), "42");
        assert_eq!(encoder.encode(&Value::from(-17)).unwrap(), "-17");
        assert_eq!(encoder.encode(&Value::from(3.14)).unwrap(), "3.14");
    }

    #[test]
    fn test_encode_string_escaping() {
        let encoder = JsonEncoder::new(false);

        assert_eq!(encoder.encode(&Value::from("hello")).unwrap(), r#""hello""#);
        assert_eq!(
            encoder.encode(&Value::from("has\"quote")).unwrap(),
            r#""has\"quote""#
        );
        assert_eq!(
            encoder.encode(&Value::from("has\nnewline")).unwrap(),
            r#""has\nnewline""#
        );
    }

    #[test]
    fn test_encode_array() {
        let encoder = JsonEncoder::new(false);

        let arr = Value::Array(vec![Value::from(1), Value::from(2), Value::from(3)]);
        assert_eq!(encoder.encode(&arr).unwrap(), "[1,2,3]");
    }

    #[test]
    fn test_encode_object() {
        let encoder = JsonEncoder::new(false);

        let mut obj = IndexMap::new();
        obj.insert("a".to_string(), Value::from(1));
        obj.insert("b".to_string(), Value::from(2));

        let result = encoder.encode(&Value::Object(obj)).unwrap();
        assert_eq!(result, r#"{"a":1,"b":2}"#);
    }

    #[test]
    fn test_encode_sorted_keys() {
        let encoder = JsonEncoder::new(true);

        let mut obj = IndexMap::new();
        obj.insert("zebra".to_string(), Value::from(1));
        obj.insert("apple".to_string(), Value::from(2));
        obj.insert("mango".to_string(), Value::from(3));

        let result = encoder.encode(&Value::Object(obj)).unwrap();
        assert_eq!(result, r#"{"apple":2,"mango":3,"zebra":1}"#);
    }
}
