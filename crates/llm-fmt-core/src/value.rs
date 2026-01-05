//! Core value type for all operations.
//!
//! This module defines the [`Value`] enum which represents any structured data
//! that can be processed by llm-fmt. It mirrors `serde_json::Value` but uses
//! [`IndexMap`] to preserve insertion order of object keys.

use indexmap::IndexMap;
use std::fmt;

/// Represents a numeric value (integer or floating-point).
#[derive(Debug, Clone, PartialEq)]
pub enum Number {
    /// Signed 64-bit integer.
    Int(i64),
    /// Unsigned 64-bit integer.
    UInt(u64),
    /// 64-bit floating-point number.
    Float(f64),
}

impl Number {
    /// Returns the number as an `i64` if it fits.
    #[must_use]
    pub fn as_i64(&self) -> Option<i64> {
        match self {
            Self::Int(n) => Some(*n),
            Self::UInt(n) => i64::try_from(*n).ok(),
            Self::Float(n) => {
                if n.fract() == 0.0 && *n >= i64::MIN as f64 && *n <= i64::MAX as f64 {
                    Some(*n as i64)
                } else {
                    None
                }
            }
        }
    }

    /// Returns the number as a `u64` if it fits.
    #[must_use]
    pub fn as_u64(&self) -> Option<u64> {
        match self {
            Self::Int(n) => u64::try_from(*n).ok(),
            Self::UInt(n) => Some(*n),
            Self::Float(n) => {
                if n.fract() == 0.0 && *n >= 0.0 && *n <= u64::MAX as f64 {
                    Some(*n as u64)
                } else {
                    None
                }
            }
        }
    }

    /// Returns the number as an `f64`.
    #[must_use]
    pub const fn as_f64(&self) -> f64 {
        match self {
            Self::Int(n) => *n as f64,
            Self::UInt(n) => *n as f64,
            Self::Float(n) => *n,
        }
    }

    /// Returns true if this is an integer (signed or unsigned).
    #[must_use]
    pub const fn is_integer(&self) -> bool {
        matches!(self, Self::Int(_) | Self::UInt(_))
    }
}

impl fmt::Display for Number {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Int(n) => write!(f, "{n}"),
            Self::UInt(n) => write!(f, "{n}"),
            Self::Float(n) => {
                // Ensure floats always have a decimal point for clarity
                if n.fract() == 0.0 {
                    write!(f, "{n}.0")
                } else {
                    write!(f, "{n}")
                }
            }
        }
    }
}

impl From<i64> for Number {
    fn from(n: i64) -> Self {
        Self::Int(n)
    }
}

impl From<u64> for Number {
    fn from(n: u64) -> Self {
        Self::UInt(n)
    }
}

impl From<f64> for Number {
    fn from(n: f64) -> Self {
        Self::Float(n)
    }
}

impl From<i32> for Number {
    fn from(n: i32) -> Self {
        Self::Int(i64::from(n))
    }
}

impl From<u32> for Number {
    fn from(n: u32) -> Self {
        Self::UInt(u64::from(n))
    }
}

impl From<f32> for Number {
    fn from(n: f32) -> Self {
        Self::Float(f64::from(n))
    }
}

/// Core value type for all operations.
///
/// Represents any structured data that can be processed by llm-fmt.
/// Uses [`IndexMap`] for objects to preserve insertion order.
#[derive(Debug, Clone, PartialEq)]
#[derive(Default)]
pub enum Value {
    /// Represents a null value.
    #[default]
    Null,
    /// Represents a boolean.
    Bool(bool),
    /// Represents a number (integer or float).
    Number(Number),
    /// Represents a string.
    String(String),
    /// Represents an array of values.
    Array(Vec<Self>),
    /// Represents an object (key-value map with preserved order).
    Object(IndexMap<String, Self>),
}

impl Value {
    /// Returns true if this value is null.
    #[must_use]
    pub const fn is_null(&self) -> bool {
        matches!(self, Self::Null)
    }

    /// Returns true if this value is a boolean.
    #[must_use]
    pub const fn is_bool(&self) -> bool {
        matches!(self, Self::Bool(_))
    }

    /// Returns true if this value is a number.
    #[must_use]
    pub const fn is_number(&self) -> bool {
        matches!(self, Self::Number(_))
    }

    /// Returns true if this value is a string.
    #[must_use]
    pub const fn is_string(&self) -> bool {
        matches!(self, Self::String(_))
    }

    /// Returns true if this value is an array.
    #[must_use]
    pub const fn is_array(&self) -> bool {
        matches!(self, Self::Array(_))
    }

    /// Returns true if this value is an object.
    #[must_use]
    pub const fn is_object(&self) -> bool {
        matches!(self, Self::Object(_))
    }

    /// Returns the boolean value if this is a Bool.
    #[must_use]
    pub const fn as_bool(&self) -> Option<bool> {
        match self {
            Self::Bool(b) => Some(*b),
            _ => None,
        }
    }

    /// Returns a reference to the number if this is a Number.
    #[must_use]
    pub const fn as_number(&self) -> Option<&Number> {
        match self {
            Self::Number(n) => Some(n),
            _ => None,
        }
    }

    /// Returns a reference to the string if this is a String.
    #[must_use]
    pub fn as_str(&self) -> Option<&str> {
        match self {
            Self::String(s) => Some(s),
            _ => None,
        }
    }

    /// Returns a reference to the array if this is an Array.
    #[must_use]
    pub const fn as_array(&self) -> Option<&Vec<Self>> {
        match self {
            Self::Array(a) => Some(a),
            _ => None,
        }
    }

    /// Returns a mutable reference to the array if this is an Array.
    #[must_use]
    pub const fn as_array_mut(&mut self) -> Option<&mut Vec<Self>> {
        match self {
            Self::Array(a) => Some(a),
            _ => None,
        }
    }

    /// Returns a reference to the object if this is an Object.
    #[must_use]
    pub const fn as_object(&self) -> Option<&IndexMap<String, Self>> {
        match self {
            Self::Object(o) => Some(o),
            _ => None,
        }
    }

    /// Returns a mutable reference to the object if this is an Object.
    #[must_use]
    pub const fn as_object_mut(&mut self) -> Option<&mut IndexMap<String, Self>> {
        match self {
            Self::Object(o) => Some(o),
            _ => None,
        }
    }

    /// Gets a value by key if this is an Object.
    #[must_use]
    pub fn get(&self, key: &str) -> Option<&Self> {
        self.as_object().and_then(|o| o.get(key))
    }

    /// Gets a value by index if this is an Array.
    #[must_use]
    pub fn get_index(&self, index: usize) -> Option<&Self> {
        self.as_array().and_then(|a| a.get(index))
    }
}


impl fmt::Display for Value {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Null => write!(f, "null"),
            Self::Bool(b) => write!(f, "{b}"),
            Self::Number(n) => write!(f, "{n}"),
            Self::String(s) => write!(f, "\"{s}\""),
            Self::Array(a) => {
                write!(f, "[")?;
                for (i, v) in a.iter().enumerate() {
                    if i > 0 {
                        write!(f, ", ")?;
                    }
                    write!(f, "{v}")?;
                }
                write!(f, "]")
            }
            Self::Object(o) => {
                write!(f, "{{")?;
                for (i, (k, v)) in o.iter().enumerate() {
                    if i > 0 {
                        write!(f, ", ")?;
                    }
                    write!(f, "\"{k}\": {v}")?;
                }
                write!(f, "}}")
            }
        }
    }
}

// Convenience From implementations
impl From<bool> for Value {
    fn from(b: bool) -> Self {
        Self::Bool(b)
    }
}

impl From<i64> for Value {
    fn from(n: i64) -> Self {
        Self::Number(Number::Int(n))
    }
}

impl From<u64> for Value {
    fn from(n: u64) -> Self {
        Self::Number(Number::UInt(n))
    }
}

impl From<i32> for Value {
    fn from(n: i32) -> Self {
        Self::Number(Number::Int(i64::from(n)))
    }
}

impl From<u32> for Value {
    fn from(n: u32) -> Self {
        Self::Number(Number::UInt(u64::from(n)))
    }
}

impl From<f64> for Value {
    fn from(n: f64) -> Self {
        Self::Number(Number::Float(n))
    }
}

impl From<f32> for Value {
    fn from(n: f32) -> Self {
        Self::Number(Number::Float(f64::from(n)))
    }
}

impl From<String> for Value {
    fn from(s: String) -> Self {
        Self::String(s)
    }
}

impl From<&str> for Value {
    fn from(s: &str) -> Self {
        Self::String(s.to_owned())
    }
}

impl<T: Into<Self>> From<Vec<T>> for Value {
    fn from(v: Vec<T>) -> Self {
        Self::Array(v.into_iter().map(Into::into).collect())
    }
}

impl From<IndexMap<String, Self>> for Value {
    fn from(m: IndexMap<String, Self>) -> Self {
        Self::Object(m)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_number_conversions() {
        let n = Number::Int(42);
        assert_eq!(n.as_i64(), Some(42));
        assert_eq!(n.as_u64(), Some(42));
        assert!((n.as_f64() - 42.0).abs() < f64::EPSILON);

        let n = Number::Float(3.14);
        assert_eq!(n.as_i64(), None);
        assert!((n.as_f64() - 3.14).abs() < f64::EPSILON);
    }

    #[test]
    fn test_value_accessors() {
        let v = Value::Bool(true);
        assert!(v.is_bool());
        assert_eq!(v.as_bool(), Some(true));

        let v = Value::String("hello".into());
        assert!(v.is_string());
        assert_eq!(v.as_str(), Some("hello"));

        let v = Value::Array(vec![Value::from(1), Value::from(2)]);
        assert!(v.is_array());
        assert_eq!(v.as_array().map(Vec::len), Some(2));
    }

    #[test]
    fn test_value_get() {
        let mut obj = IndexMap::new();
        obj.insert("name".into(), Value::from("Alice"));
        obj.insert("age".into(), Value::from(30));
        let v = Value::Object(obj);

        assert_eq!(v.get("name").and_then(Value::as_str), Some("Alice"));
        assert_eq!(v.get("age").and_then(|v| v.as_number()?.as_i64()), Some(30));
        assert!(v.get("missing").is_none());
    }
}
