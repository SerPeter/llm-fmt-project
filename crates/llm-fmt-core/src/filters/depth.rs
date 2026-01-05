//! Max depth filter for limiting data nesting.

use indexmap::IndexMap;

use crate::{Result, Value};

use super::Filter;

/// Filter that truncates data beyond a specified depth.
#[derive(Debug, Clone)]
pub struct MaxDepthFilter {
    /// Maximum nesting depth to keep (0 = root only).
    max_depth: usize,
}

impl MaxDepthFilter {
    /// Create a new max depth filter.
    ///
    /// # Errors
    ///
    /// Returns an error if `max_depth` is invalid (this implementation
    /// accepts all values, but the error type is for future extensibility).
    pub const fn new(max_depth: usize) -> Result<Self> {
        Ok(Self { max_depth })
    }

    /// Recursively truncate data at the given depth.
    fn truncate(&self, value: Value, current_depth: usize) -> Value {
        if current_depth >= self.max_depth {
            return self.placeholder(&value);
        }

        match value {
            Value::Object(obj) => {
                let truncated: IndexMap<String, Value> = obj
                    .into_iter()
                    .map(|(k, v)| (k, self.truncate(v, current_depth + 1)))
                    .collect();
                Value::Object(truncated)
            }
            Value::Array(arr) => {
                let truncated: Vec<Value> = arr
                    .into_iter()
                    .map(|v| self.truncate(v, current_depth + 1))
                    .collect();
                Value::Array(truncated)
            }
            other => other,
        }
    }

    /// Create a placeholder for truncated values.
    fn placeholder(&self, value: &Value) -> Value {
        match value {
            Value::Object(obj) => {
                let mut placeholder = IndexMap::new();
                placeholder.insert(
                    "...".to_string(),
                    Value::String(format!("{} keys", obj.len())),
                );
                Value::Object(placeholder)
            }
            Value::Array(arr) => {
                Value::Array(vec![Value::String(format!("... {} items", arr.len()))])
            }
            other => other.clone(),
        }
    }
}

impl Filter for MaxDepthFilter {
    fn apply(&self, value: Value) -> Result<Value> {
        Ok(self.truncate(value, 0))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_nested(depth: usize) -> Value {
        if depth == 0 {
            Value::from("leaf")
        } else {
            let mut obj = IndexMap::new();
            obj.insert("child".to_string(), make_nested(depth - 1));
            obj.insert("value".to_string(), Value::from(depth as i64));
            Value::Object(obj)
        }
    }

    #[test]
    fn test_depth_zero() {
        let filter = MaxDepthFilter::new(0).unwrap();
        let data = make_nested(3);
        let result = filter.apply(data).unwrap();

        // At depth 0, the root object should be replaced with placeholder
        assert!(result.is_object());
        let obj = result.as_object().unwrap();
        assert!(obj.contains_key("..."));
    }

    #[test]
    fn test_depth_one() {
        let filter = MaxDepthFilter::new(1).unwrap();
        let data = make_nested(3);
        let result = filter.apply(data).unwrap();

        // At depth 1, we should see the first level but children truncated
        assert!(result.is_object());
        let obj = result.as_object().unwrap();
        assert!(obj.contains_key("child"));
        assert!(obj.contains_key("value"));

        // Child should be a placeholder
        let child = obj.get("child").unwrap();
        assert!(child.is_object());
        let child_obj = child.as_object().unwrap();
        assert!(child_obj.contains_key("..."));
    }

    #[test]
    fn test_array_truncation() {
        let filter = MaxDepthFilter::new(1).unwrap();

        let mut obj = IndexMap::new();
        obj.insert(
            "items".to_string(),
            Value::Array(vec![
                Value::from(1),
                Value::from(2),
                Value::from(3),
            ]),
        );
        let data = Value::Object(obj);

        let result = filter.apply(data).unwrap();
        let items = result.get("items").unwrap();

        // Array at depth 1 should be replaced with placeholder
        assert!(items.is_array());
        let arr = items.as_array().unwrap();
        assert_eq!(arr.len(), 1);
        assert!(arr[0].as_str().unwrap().contains("3 items"));
    }

    #[test]
    fn test_primitives_unchanged() {
        let filter = MaxDepthFilter::new(0).unwrap();

        assert_eq!(filter.apply(Value::Null).unwrap(), Value::Null);
        assert_eq!(filter.apply(Value::from(42)).unwrap(), Value::from(42));
        assert_eq!(
            filter.apply(Value::from("hello")).unwrap(),
            Value::from("hello")
        );
    }
}
