//! Data shape detection for format recommendation.
//!
//! This module analyzes data structures to determine their shape,
//! which is used to recommend the optimal output format.

use crate::Value;

/// Describes the shape and structure of data.
#[derive(Debug, Clone, Default)]
pub struct DataShape {
    /// Whether the root is an array.
    pub is_array: bool,
    /// Whether the root is a uniform array of objects with identical keys.
    pub is_uniform_array: bool,
    /// Length of the array (if root is array).
    pub array_length: usize,
    /// Number of fields (for uniform arrays or objects).
    pub field_count: usize,
    /// Maximum nesting depth.
    pub max_depth: usize,
    /// Whether the data is mostly primitive values (>70%).
    pub is_mostly_primitives: bool,
    /// Human-readable description of the data shape.
    pub description: String,
    /// Sample of field keys (up to 10).
    pub sample_keys: Vec<String>,
}

impl DataShape {
    /// Create a new empty DataShape.
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }
}

/// Detect the shape and structure of data.
///
/// Samples large arrays for efficiency (up to `max_sample` items).
#[must_use]
pub fn detect_data_shape(value: &Value, max_sample: usize) -> DataShape {
    match value {
        Value::Array(arr) => analyze_array(arr, max_sample),
        Value::Object(obj) => analyze_object(obj),
        _ => DataShape {
            description: format!("Primitive value ({})", primitive_type_name(value)),
            is_mostly_primitives: true,
            ..Default::default()
        },
    }
}

/// Detect data shape with default sample size of 100.
#[must_use]
pub fn detect(value: &Value) -> DataShape {
    detect_data_shape(value, 100)
}

/// Select the optimal output format based on data shape.
///
/// Returns one of: "toon", "yaml", "json"
#[must_use]
pub fn select_format(value: &Value) -> &'static str {
    let shape = detect(value);

    // Uniform arrays benefit most from TOON
    if shape.is_uniform_array && shape.array_length > 1 {
        return "toon";
    }

    // Shallow structures with mostly primitives work well in YAML
    if shape.max_depth <= 2 && shape.is_mostly_primitives {
        return "yaml";
    }

    // Default to compact JSON for complex structures
    "json"
}

fn analyze_array(arr: &[Value], max_sample: usize) -> DataShape {
    let mut shape = DataShape {
        is_array: true,
        array_length: arr.len(),
        ..Default::default()
    };

    if arr.is_empty() {
        shape.description = "Empty array".to_string();
        shape.max_depth = 1;
        shape.is_mostly_primitives = true;
        return shape;
    }

    // Sample large arrays for efficiency
    let sample: Vec<&Value> = arr.iter().take(max_sample).collect();

    // Check if all items are objects
    let all_objects = sample.iter().all(|v| matches!(v, Value::Object(_)));

    if all_objects {
        // Check if uniform (all objects have same keys)
        if let Some(first_keys) = get_object_keys(&sample[0]) {
            let is_uniform = sample.iter().skip(1).all(|v| {
                get_object_keys(v).map_or(false, |keys| keys == first_keys)
            });

            if is_uniform {
                shape.is_uniform_array = true;
                shape.field_count = first_keys.len();
                shape.sample_keys = first_keys.into_iter().take(10).collect();
                shape.description = format!(
                    "Uniform array of {} objects with {} fields",
                    shape.array_length, shape.field_count
                );
            } else {
                shape.description = format!(
                    "Array of {} objects with varying schemas",
                    shape.array_length
                );
            }
        }
    } else if sample.iter().all(|v| is_primitive(v)) {
        shape.description = format!("Array of {} primitives", shape.array_length);
        shape.is_mostly_primitives = true;
    } else {
        shape.description = format!("Mixed array of {} items", shape.array_length);
    }

    // Calculate depth from sample
    shape.max_depth = sample
        .iter()
        .map(|v| calculate_depth(v, 0))
        .max()
        .unwrap_or(0)
        + 1; // +1 for array level

    // Check if mostly primitives
    shape.is_mostly_primitives = check_mostly_primitives_sampled(&sample);

    shape
}

fn analyze_object(obj: &indexmap::IndexMap<String, Value>) -> DataShape {
    let mut shape = DataShape {
        field_count: obj.len(),
        sample_keys: obj.keys().take(10).cloned().collect(),
        ..Default::default()
    };

    if obj.is_empty() {
        shape.description = "Empty object".to_string();
        shape.max_depth = 1;
        shape.is_mostly_primitives = true;
        return shape;
    }

    let nested_count = obj.values().filter(|v| matches!(v, Value::Object(_) | Value::Array(_))).count();

    if nested_count == 0 {
        shape.description = format!("Flat object with {} fields", obj.len());
    } else {
        shape.description = format!("Nested object with {} top-level fields", obj.len());
    }

    shape.max_depth = calculate_depth(&Value::Object(obj.clone()), 0);
    shape.is_mostly_primitives = check_mostly_primitives(&Value::Object(obj.clone()));

    shape
}

fn get_object_keys(value: &Value) -> Option<Vec<String>> {
    match value {
        Value::Object(obj) => Some(obj.keys().cloned().collect()),
        _ => None,
    }
}

fn is_primitive(value: &Value) -> bool {
    matches!(
        value,
        Value::Null | Value::Bool(_) | Value::Number(_) | Value::String(_)
    )
}

fn primitive_type_name(value: &Value) -> &'static str {
    match value {
        Value::Null => "null",
        Value::Bool(_) => "boolean",
        Value::Number(_) => "number",
        Value::String(_) => "string",
        Value::Array(_) => "array",
        Value::Object(_) => "object",
    }
}

fn calculate_depth(value: &Value, current: usize) -> usize {
    match value {
        Value::Object(obj) => {
            if obj.is_empty() {
                current
            } else {
                obj.values()
                    .map(|v| calculate_depth(v, current + 1))
                    .max()
                    .unwrap_or(current)
            }
        }
        Value::Array(arr) => {
            if arr.is_empty() {
                current
            } else {
                arr.iter()
                    .map(|v| calculate_depth(v, current + 1))
                    .max()
                    .unwrap_or(current)
            }
        }
        _ => current,
    }
}

fn check_mostly_primitives_sampled(sample: &[&Value]) -> bool {
    if sample.is_empty() {
        return true;
    }

    // Check if it's an array of primitives
    if sample.iter().all(|v| is_primitive(v)) {
        return true;
    }

    let mut primitive_count = 0usize;
    let mut complex_count = 0usize;

    for item in sample {
        count_primitives_in_value(item, &mut primitive_count, &mut complex_count);
    }

    let total = primitive_count + complex_count;
    total == 0 || (primitive_count as f64 / total as f64) >= 0.7
}

fn check_mostly_primitives(value: &Value) -> bool {
    let mut primitive_count = 0usize;
    let mut complex_count = 0usize;

    count_primitives_in_value(value, &mut primitive_count, &mut complex_count);

    let total = primitive_count + complex_count;
    total == 0 || (primitive_count as f64 / total as f64) >= 0.7
}

fn count_primitives_in_value(value: &Value, primitive_count: &mut usize, complex_count: &mut usize) {
    match value {
        Value::Object(obj) => {
            for v in obj.values() {
                if matches!(v, Value::Object(_) | Value::Array(_)) {
                    *complex_count += 1;
                    count_primitives_in_value(v, primitive_count, complex_count);
                } else {
                    *primitive_count += 1;
                }
            }
        }
        Value::Array(arr) => {
            for item in arr {
                if matches!(item, Value::Object(_) | Value::Array(_)) {
                    *complex_count += 1;
                    count_primitives_in_value(item, primitive_count, complex_count);
                } else {
                    *primitive_count += 1;
                }
            }
        }
        _ => {
            *primitive_count += 1;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use indexmap::IndexMap;

    fn make_uniform_array() -> Value {
        Value::Array(vec![
            {
                let mut obj = IndexMap::new();
                obj.insert("id".to_string(), Value::from(1));
                obj.insert("name".to_string(), Value::from("Alice"));
                Value::Object(obj)
            },
            {
                let mut obj = IndexMap::new();
                obj.insert("id".to_string(), Value::from(2));
                obj.insert("name".to_string(), Value::from("Bob"));
                Value::Object(obj)
            },
        ])
    }

    fn make_non_uniform_array() -> Value {
        Value::Array(vec![
            {
                let mut obj = IndexMap::new();
                obj.insert("id".to_string(), Value::from(1));
                Value::Object(obj)
            },
            {
                let mut obj = IndexMap::new();
                obj.insert("name".to_string(), Value::from("Bob"));
                Value::Object(obj)
            },
        ])
    }

    fn make_flat_object() -> Value {
        let mut obj = IndexMap::new();
        obj.insert("host".to_string(), Value::from("localhost"));
        obj.insert("port".to_string(), Value::from(5432));
        Value::Object(obj)
    }

    fn make_deep_nested() -> Value {
        let mut d = IndexMap::new();
        d.insert("value".to_string(), Value::from(1));
        let mut c = IndexMap::new();
        c.insert("d".to_string(), Value::Object(d));
        let mut b = IndexMap::new();
        b.insert("c".to_string(), Value::Object(c));
        let mut a = IndexMap::new();
        a.insert("b".to_string(), Value::Object(b));
        let mut root = IndexMap::new();
        root.insert("a".to_string(), Value::Object(a));
        Value::Object(root)
    }

    #[test]
    fn test_detect_uniform_array() {
        let data = make_uniform_array();
        let shape = detect(&data);

        assert!(shape.is_array);
        assert!(shape.is_uniform_array);
        assert_eq!(shape.array_length, 2);
        assert_eq!(shape.field_count, 2);
        assert!(shape.description.contains("Uniform array"));
    }

    #[test]
    fn test_detect_non_uniform_array() {
        let data = make_non_uniform_array();
        let shape = detect(&data);

        assert!(shape.is_array);
        assert!(!shape.is_uniform_array);
        assert_eq!(shape.array_length, 2);
        assert!(shape.description.contains("varying schemas"));
    }

    #[test]
    fn test_detect_flat_object() {
        let data = make_flat_object();
        let shape = detect(&data);

        assert!(!shape.is_array);
        assert_eq!(shape.field_count, 2);
        assert!(shape.is_mostly_primitives);
        assert!(shape.description.contains("Flat object"));
    }

    #[test]
    fn test_detect_deep_nested() {
        let data = make_deep_nested();
        let shape = detect(&data);

        assert!(!shape.is_array);
        assert!(shape.max_depth > 2);
        assert!(shape.description.contains("Nested object"));
    }

    #[test]
    fn test_detect_primitive_array() {
        let data = Value::Array(vec![Value::from(1), Value::from(2), Value::from(3)]);
        let shape = detect(&data);

        assert!(shape.is_array);
        assert!(!shape.is_uniform_array);
        assert!(shape.is_mostly_primitives);
        assert!(shape.description.contains("primitives"));
    }

    #[test]
    fn test_select_format_uniform_array() {
        let data = make_uniform_array();
        assert_eq!(select_format(&data), "toon");
    }

    #[test]
    fn test_select_format_flat_object() {
        let data = make_flat_object();
        assert_eq!(select_format(&data), "yaml");
    }

    #[test]
    fn test_select_format_deep_nested() {
        let data = make_deep_nested();
        assert_eq!(select_format(&data), "json");
    }

    #[test]
    fn test_empty_array() {
        let data = Value::Array(vec![]);
        let shape = detect(&data);

        assert!(shape.is_array);
        assert_eq!(shape.array_length, 0);
        assert!(shape.description.contains("Empty"));
    }

    #[test]
    fn test_empty_object() {
        let data = Value::Object(IndexMap::new());
        let shape = detect(&data);

        assert!(!shape.is_array);
        assert_eq!(shape.field_count, 0);
        assert!(shape.description.contains("Empty"));
    }

    #[test]
    fn test_sample_keys() {
        let data = make_uniform_array();
        let shape = detect(&data);

        assert!(!shape.sample_keys.is_empty());
        assert!(shape.sample_keys.contains(&"id".to_string()) || shape.sample_keys.contains(&"name".to_string()));
    }
}
