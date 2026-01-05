//! Include filter for extracting data by path.
//!
//! Supports simple path expressions like:
//! - `users` - get the "users" key
//! - `users[0]` - get first element of "users" array
//! - `users[*].name` - get "name" from all users
//! - `data.items` - nested path

use crate::error::FilterError;
use crate::value::Value;
use crate::Result;

use super::Filter;

/// Filter that extracts data matching a path expression.
#[derive(Debug, Clone)]
pub struct IncludeFilter {
    /// The path expression.
    expression: String,
    /// Parsed path segments.
    segments: Vec<PathSegment>,
}

/// A segment of a path expression.
#[derive(Debug, Clone)]
enum PathSegment {
    /// Object key access.
    Key(String),
    /// Array index access.
    Index(usize),
    /// Wildcard - all array elements.
    Wildcard,
}

impl IncludeFilter {
    /// Create a new include filter.
    ///
    /// # Errors
    ///
    /// Returns an error if the expression is invalid.
    pub fn new(expression: &str) -> Result<Self> {
        let segments = Self::parse_expression(expression)?;
        Ok(Self {
            expression: expression.to_string(),
            segments,
        })
    }

    /// Parse a path expression into segments.
    fn parse_expression(expr: &str) -> Result<Vec<PathSegment>> {
        let mut segments = Vec::new();
        let mut current = String::new();
        let mut chars = expr.chars().peekable();

        while let Some(c) = chars.next() {
            match c {
                '.' => {
                    if !current.is_empty() {
                        segments.push(PathSegment::Key(current.clone()));
                        current.clear();
                    }
                }
                '[' => {
                    if !current.is_empty() {
                        segments.push(PathSegment::Key(current.clone()));
                        current.clear();
                    }

                    // Parse bracket content
                    let mut bracket_content = String::new();
                    while let Some(&next) = chars.peek() {
                        if next == ']' {
                            chars.next();
                            break;
                        }
                        bracket_content.push(chars.next().unwrap());
                    }

                    if bracket_content == "*" {
                        segments.push(PathSegment::Wildcard);
                    } else if let Ok(idx) = bracket_content.parse::<usize>() {
                        segments.push(PathSegment::Index(idx));
                    } else {
                        // Treat as key (for quoted keys)
                        let key = bracket_content
                            .trim_matches(|c| c == '"' || c == '\'')
                            .to_string();
                        segments.push(PathSegment::Key(key));
                    }
                }
                _ => {
                    current.push(c);
                }
            }
        }

        if !current.is_empty() {
            segments.push(PathSegment::Key(current));
        }

        if segments.is_empty() {
            return Err(FilterError::InvalidExpression(format!(
                "Empty path expression: {expr}"
            ))
            .into());
        }

        Ok(segments)
    }

    /// Extract value at the given path.
    fn extract(&self, value: &Value) -> Value {
        self.extract_segments(value, &self.segments)
    }

    /// Recursively extract value following path segments.
    fn extract_segments(&self, value: &Value, segments: &[PathSegment]) -> Value {
        if segments.is_empty() {
            return value.clone();
        }

        let (segment, rest) = segments.split_first().unwrap();

        match segment {
            PathSegment::Key(key) => {
                if let Some(obj) = value.as_object() {
                    if let Some(child) = obj.get(key) {
                        return self.extract_segments(child, rest);
                    }
                }
                Value::Null
            }
            PathSegment::Index(idx) => {
                if let Some(arr) = value.as_array() {
                    if let Some(child) = arr.get(*idx) {
                        return self.extract_segments(child, rest);
                    }
                }
                Value::Null
            }
            PathSegment::Wildcard => {
                if let Some(arr) = value.as_array() {
                    let results: Vec<Value> = arr
                        .iter()
                        .map(|item| self.extract_segments(item, rest))
                        .filter(|v| !v.is_null())
                        .collect();
                    return Value::Array(results);
                }
                Value::Null
            }
        }
    }
}

impl Filter for IncludeFilter {
    fn apply(&self, value: Value) -> Result<Value> {
        let result = self.extract(&value);
        // Return original if no match
        if result.is_null() {
            Ok(value)
        } else {
            Ok(result)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use indexmap::IndexMap;

    fn make_test_data() -> Value {
        let mut user1 = IndexMap::new();
        user1.insert("name".to_string(), Value::from("Alice"));
        user1.insert("age".to_string(), Value::from(30));

        let mut user2 = IndexMap::new();
        user2.insert("name".to_string(), Value::from("Bob"));
        user2.insert("age".to_string(), Value::from(25));

        let mut data = IndexMap::new();
        data.insert(
            "users".to_string(),
            Value::Array(vec![Value::Object(user1), Value::Object(user2)]),
        );
        data.insert("count".to_string(), Value::from(2));

        Value::Object(data)
    }

    #[test]
    fn test_simple_key() {
        let filter = IncludeFilter::new("count").unwrap();
        let data = make_test_data();
        let result = filter.apply(data).unwrap();

        assert_eq!(result.as_number().and_then(|n| n.as_i64()), Some(2));
    }

    #[test]
    fn test_nested_key() {
        let filter = IncludeFilter::new("users").unwrap();
        let data = make_test_data();
        let result = filter.apply(data).unwrap();

        assert!(result.is_array());
        assert_eq!(result.as_array().unwrap().len(), 2);
    }

    #[test]
    fn test_array_index() {
        let filter = IncludeFilter::new("users[0]").unwrap();
        let data = make_test_data();
        let result = filter.apply(data).unwrap();

        assert!(result.is_object());
        assert_eq!(result.get("name").and_then(Value::as_str), Some("Alice"));
    }

    #[test]
    fn test_array_index_nested() {
        let filter = IncludeFilter::new("users[1].name").unwrap();
        let data = make_test_data();
        let result = filter.apply(data).unwrap();

        assert_eq!(result.as_str(), Some("Bob"));
    }

    #[test]
    fn test_wildcard() {
        let filter = IncludeFilter::new("users[*].name").unwrap();
        let data = make_test_data();
        let result = filter.apply(data).unwrap();

        let arr = result.as_array().unwrap();
        assert_eq!(arr.len(), 2);
        assert_eq!(arr[0].as_str(), Some("Alice"));
        assert_eq!(arr[1].as_str(), Some("Bob"));
    }

    #[test]
    fn test_nonexistent_path() {
        let filter = IncludeFilter::new("nonexistent").unwrap();
        let data = make_test_data();
        let result = filter.apply(data.clone()).unwrap();

        // Returns original data when path doesn't exist
        assert_eq!(result, data);
    }

    #[test]
    fn test_dot_notation() {
        let mut inner = IndexMap::new();
        inner.insert("value".to_string(), Value::from(42));

        let mut outer = IndexMap::new();
        outer.insert("nested".to_string(), Value::Object(inner));

        let data = Value::Object(outer);
        let filter = IncludeFilter::new("nested.value").unwrap();
        let result = filter.apply(data).unwrap();

        assert_eq!(result.as_number().and_then(|n| n.as_i64()), Some(42));
    }
}
