//! Benchmark data generators.
//!
//! This module provides functions to generate synthetic benchmark data
//! with realistic shapes for performance testing.

use indexmap::IndexMap;

use crate::{Number, Value};

/// Generate an API-response-like array of uniform objects.
///
/// Each object has: id, name, email, active, score, created_at
#[must_use]
pub fn generate_api_response(count: usize) -> Value {
    Value::Array(
        (0..count)
            .map(|i| {
                let mut obj = IndexMap::new();
                obj.insert("id".to_string(), Value::Number(Number::UInt(i as u64)));
                obj.insert("name".to_string(), Value::String(format!("User {i}")));
                obj.insert(
                    "email".to_string(),
                    Value::String(format!("user{i}@example.com")),
                );
                obj.insert("active".to_string(), Value::Bool(i % 2 == 0));
                obj.insert(
                    "score".to_string(),
                    Value::Number(Number::UInt((i * 17 % 100) as u64)),
                );
                obj.insert(
                    "created_at".to_string(),
                    Value::String("2024-01-15T10:30:00Z".to_string()),
                );
                obj.insert(
                    "department".to_string(),
                    Value::String(
                        ["Engineering", "Sales", "Marketing", "Support"][i % 4].to_string(),
                    ),
                );
                obj.insert(
                    "level".to_string(),
                    Value::Number(Number::UInt((i % 5 + 1) as u64)),
                );
                Value::Object(obj)
            })
            .collect(),
    )
}

/// Generate a deeply nested configuration object.
///
/// Creates a tree structure with the specified depth.
#[must_use]
pub fn generate_nested_config(depth: usize) -> Value {
    fn nest(level: usize, max: usize) -> Value {
        if level >= max {
            let mut leaf = IndexMap::new();
            leaf.insert("value".to_string(), Value::String("leaf_value".to_string()));
            leaf.insert("enabled".to_string(), Value::Bool(true));
            return Value::Object(leaf);
        }

        let mut obj = IndexMap::new();
        obj.insert(
            "level".to_string(),
            Value::Number(Number::UInt(level as u64)),
        );
        obj.insert(
            "name".to_string(),
            Value::String(format!("config_level_{level}")),
        );

        let mut settings = IndexMap::new();
        settings.insert("enabled".to_string(), Value::Bool(true));
        settings.insert(
            "timeout".to_string(),
            Value::Number(Number::UInt((level * 1000) as u64)),
        );
        settings.insert(
            "retries".to_string(),
            Value::Number(Number::UInt((3 + level) as u64)),
        );
        obj.insert("settings".to_string(), Value::Object(settings));

        obj.insert("child".to_string(), nest(level + 1, max));

        // Add a sibling branch for variety
        if level < max / 2 {
            obj.insert("alternate".to_string(), nest(level + 2, max));
        }

        Value::Object(obj)
    }
    nest(0, depth)
}

/// Generate data with mixed/heterogeneous types.
///
/// Contains arrays with varying object shapes, null values, nested arrays.
#[must_use]
pub fn generate_mixed_types(count: usize) -> Value {
    Value::Array(
        (0..count)
            .map(|i| {
                let mut obj = IndexMap::new();
                obj.insert("id".to_string(), Value::Number(Number::UInt(i as u64)));

                // Vary the fields based on index
                match i % 5 {
                    0 => {
                        obj.insert(
                            "type".to_string(),
                            Value::String("text".to_string()),
                        );
                        obj.insert(
                            "content".to_string(),
                            Value::String(format!("This is item {i} with some longer text content that varies.")),
                        );
                    }
                    1 => {
                        obj.insert(
                            "type".to_string(),
                            Value::String("number".to_string()),
                        );
                        obj.insert(
                            "value".to_string(),
                            Value::Number(Number::Float(i as f64 * 3.14159)),
                        );
                        obj.insert("precision".to_string(), Value::Number(Number::UInt(6)));
                    }
                    2 => {
                        obj.insert(
                            "type".to_string(),
                            Value::String("array".to_string()),
                        );
                        obj.insert(
                            "items".to_string(),
                            Value::Array(
                                (0..5)
                                    .map(|j| Value::Number(Number::UInt((i * 10 + j) as u64)))
                                    .collect(),
                            ),
                        );
                    }
                    3 => {
                        obj.insert(
                            "type".to_string(),
                            Value::String("nested".to_string()),
                        );
                        let mut inner = IndexMap::new();
                        inner.insert("x".to_string(), Value::Number(Number::Int(i as i64)));
                        inner.insert("y".to_string(), Value::Number(Number::Int(-(i as i64))));
                        inner.insert(
                            "label".to_string(),
                            Value::String(format!("point_{i}")),
                        );
                        obj.insert("data".to_string(), Value::Object(inner));
                    }
                    _ => {
                        obj.insert(
                            "type".to_string(),
                            Value::String("nullable".to_string()),
                        );
                        obj.insert("optional_field".to_string(), Value::Null);
                        obj.insert("present".to_string(), Value::Bool(i % 2 == 0));
                    }
                }

                Value::Object(obj)
            })
            .collect(),
    )
}

/// Generate a sparse array with non-uniform objects.
///
/// Each object has a different subset of possible fields.
#[must_use]
pub fn generate_sparse_array(count: usize) -> Value {
    let all_fields = [
        "id", "name", "email", "phone", "address", "city", "country", "zip", "notes", "tags",
    ];

    Value::Array(
        (0..count)
            .map(|i| {
                let mut obj = IndexMap::new();
                // Always include id
                obj.insert(
                    "id".to_string(),
                    Value::Number(Number::UInt(i as u64)),
                );

                // Include a varying subset of fields based on index
                // Use different thresholds per item to create varying field counts
                let threshold = (i % 5) + 1; // 1-5 fields threshold
                for (j, field) in all_fields.iter().enumerate().skip(1) {
                    if j <= threshold || (i * j) % 7 == 0 {
                        let value = match *field {
                            "name" => Value::String(format!("Name {i}")),
                            "email" => Value::String(format!("email{i}@test.com")),
                            "phone" => Value::String(format!("+1-555-{:04}", i % 10000)),
                            "address" => Value::String(format!("{} Main St", i * 100)),
                            "city" => Value::String(
                                ["New York", "Los Angeles", "Chicago", "Houston"][i % 4]
                                    .to_string(),
                            ),
                            "country" => Value::String("USA".to_string()),
                            "zip" => Value::String(format!("{:05}", 10000 + i)),
                            "notes" => {
                                if i % 7 == 0 {
                                    Value::Null
                                } else {
                                    Value::String(format!("Note for item {i}"))
                                }
                            }
                            "tags" => Value::Array(
                                (0..(i % 4))
                                    .map(|t| Value::String(format!("tag{t}")))
                                    .collect(),
                            ),
                            _ => Value::Null,
                        };
                        obj.insert((*field).to_string(), value);
                    }
                }

                Value::Object(obj)
            })
            .collect(),
    )
}

/// Generate tabular data suitable for CSV/TSV.
///
/// Simple flat objects with consistent fields.
#[must_use]
pub fn generate_tabular(count: usize) -> Value {
    Value::Array(
        (0..count)
            .map(|i| {
                let mut obj = IndexMap::new();
                obj.insert("row".to_string(), Value::Number(Number::UInt(i as u64)));
                obj.insert(
                    "product".to_string(),
                    Value::String(format!("Product {}", i % 50)),
                );
                obj.insert(
                    "category".to_string(),
                    Value::String(
                        ["Electronics", "Clothing", "Food", "Books", "Home"][i % 5].to_string(),
                    ),
                );
                obj.insert(
                    "price".to_string(),
                    Value::Number(Number::Float((i % 1000) as f64 * 0.99 + 0.01)),
                );
                obj.insert(
                    "quantity".to_string(),
                    Value::Number(Number::UInt((i * 7 % 100) as u64)),
                );
                obj.insert("in_stock".to_string(), Value::Bool(i % 3 != 0));
                Value::Object(obj)
            })
            .collect(),
    )
}

/// Convert a Value to JSON string for file output.
#[must_use]
pub fn value_to_json(value: &Value) -> String {
    value_to_json_pretty(value, 0)
}

fn value_to_json_pretty(value: &Value, indent: usize) -> String {
    let spaces = "  ".repeat(indent);
    let inner_spaces = "  ".repeat(indent + 1);

    match value {
        Value::Null => "null".to_string(),
        Value::Bool(b) => b.to_string(),
        Value::Number(n) => n.to_string(),
        Value::String(s) => format!("\"{}\"", escape_json_string(s)),
        Value::Array(arr) => {
            if arr.is_empty() {
                "[]".to_string()
            } else {
                let items: Vec<String> = arr
                    .iter()
                    .map(|v| format!("{inner_spaces}{}", value_to_json_pretty(v, indent + 1)))
                    .collect();
                format!("[\n{}\n{spaces}]", items.join(",\n"))
            }
        }
        Value::Object(obj) => {
            if obj.is_empty() {
                "{}".to_string()
            } else {
                let items: Vec<String> = obj
                    .iter()
                    .map(|(k, v)| {
                        format!(
                            "{inner_spaces}\"{}\": {}",
                            escape_json_string(k),
                            value_to_json_pretty(v, indent + 1)
                        )
                    })
                    .collect();
                format!("{{\n{}\n{spaces}}}", items.join(",\n"))
            }
        }
    }
}

fn escape_json_string(s: &str) -> String {
    let mut result = String::with_capacity(s.len());
    for c in s.chars() {
        match c {
            '"' => result.push_str("\\\""),
            '\\' => result.push_str("\\\\"),
            '\n' => result.push_str("\\n"),
            '\r' => result.push_str("\\r"),
            '\t' => result.push_str("\\t"),
            c if c.is_control() => result.push_str(&format!("\\u{:04x}", c as u32)),
            c => result.push(c),
        }
    }
    result
}

/// Convert a Value to YAML string for file output.
#[must_use]
pub fn value_to_yaml(value: &Value) -> String {
    value_to_yaml_inner(value, 0, true)
}

fn value_to_yaml_inner(value: &Value, indent: usize, is_root: bool) -> String {
    let spaces = "  ".repeat(indent);

    match value {
        Value::Null => "null".to_string(),
        Value::Bool(b) => b.to_string(),
        Value::Number(n) => n.to_string(),
        Value::String(s) => {
            if s.contains('\n') || s.contains(':') || s.contains('#') || s.starts_with(' ') {
                format!("\"{}\"", escape_json_string(s))
            } else {
                s.clone()
            }
        }
        Value::Array(arr) => {
            if arr.is_empty() {
                "[]".to_string()
            } else {
                let items: Vec<String> = arr
                    .iter()
                    .map(|v| {
                        let val_str = value_to_yaml_inner(v, indent + 1, false);
                        if matches!(v, Value::Object(_) | Value::Array(_)) {
                            format!("{spaces}- {}", val_str.trim_start())
                        } else {
                            format!("{spaces}- {val_str}")
                        }
                    })
                    .collect();
                if is_root {
                    items.join("\n")
                } else {
                    format!("\n{}", items.join("\n"))
                }
            }
        }
        Value::Object(obj) => {
            if obj.is_empty() {
                "{}".to_string()
            } else {
                let items: Vec<String> = obj
                    .iter()
                    .map(|(k, v)| {
                        let val_str = value_to_yaml_inner(v, indent + 1, false);
                        if matches!(v, Value::Object(_) | Value::Array(_)) {
                            format!("{spaces}{k}:{val_str}")
                        } else {
                            format!("{spaces}{k}: {val_str}")
                        }
                    })
                    .collect();
                if is_root {
                    items.join("\n")
                } else {
                    format!("\n{}", items.join("\n"))
                }
            }
        }
    }
}

/// Convert a Value (array of objects) to CSV string.
#[must_use]
pub fn value_to_csv(value: &Value) -> Option<String> {
    let arr = value.as_array()?;
    if arr.is_empty() {
        return Some(String::new());
    }

    // Get headers from first object
    let first = arr.first()?.as_object()?;
    let headers: Vec<&str> = first.keys().map(String::as_str).collect();

    let mut result = headers.join(",");
    result.push('\n');

    for item in arr {
        if let Some(obj) = item.as_object() {
            let row: Vec<String> = headers
                .iter()
                .map(|h| {
                    obj.get(*h)
                        .map_or_else(String::new, |v| csv_escape_value(v))
                })
                .collect();
            result.push_str(&row.join(","));
            result.push('\n');
        }
    }

    Some(result)
}

fn csv_escape_value(value: &Value) -> String {
    match value {
        Value::Null => String::new(),
        Value::Bool(b) => b.to_string(),
        Value::Number(n) => n.to_string(),
        Value::String(s) => {
            if s.contains(',') || s.contains('"') || s.contains('\n') {
                format!("\"{}\"", s.replace('"', "\"\""))
            } else {
                s.clone()
            }
        }
        Value::Array(_) | Value::Object(_) => "[complex]".to_string(),
    }
}

/// Convert a Value to simple XML string.
#[must_use]
pub fn value_to_xml(value: &Value, root_name: &str) -> String {
    let mut result = String::from("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
    result.push_str(&format!("<{root_name}>\n"));
    result.push_str(&value_to_xml_inner(value, 1, "item"));
    result.push_str(&format!("</{root_name}>\n"));
    result
}

fn value_to_xml_inner(value: &Value, indent: usize, tag: &str) -> String {
    let spaces = "  ".repeat(indent);

    match value {
        Value::Null => format!("{spaces}<{tag}/>\n"),
        Value::Bool(b) => format!("{spaces}<{tag}>{b}</{tag}>\n"),
        Value::Number(n) => format!("{spaces}<{tag}>{n}</{tag}>\n"),
        Value::String(s) => format!("{spaces}<{tag}>{}</{tag}>\n", escape_xml(s)),
        Value::Array(arr) => {
            let mut result = String::new();
            for item in arr {
                result.push_str(&value_to_xml_inner(item, indent, tag));
            }
            result
        }
        Value::Object(obj) => {
            let mut result = format!("{spaces}<{tag}>\n");
            for (k, v) in obj {
                result.push_str(&value_to_xml_inner(v, indent + 1, k));
            }
            result.push_str(&format!("{spaces}</{tag}>\n"));
            result
        }
    }
}

fn escape_xml(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_generate_api_response() {
        let data = generate_api_response(10);
        let arr = data.as_array().unwrap();
        assert_eq!(arr.len(), 10);

        let first = arr[0].as_object().unwrap();
        assert!(first.contains_key("id"));
        assert!(first.contains_key("name"));
        assert!(first.contains_key("email"));
    }

    #[test]
    fn test_generate_nested_config() {
        let data = generate_nested_config(5);
        assert!(data.is_object());

        // Should have nested children
        let obj = data.as_object().unwrap();
        assert!(obj.contains_key("child"));
    }

    #[test]
    fn test_generate_mixed_types() {
        let data = generate_mixed_types(10);
        let arr = data.as_array().unwrap();
        assert_eq!(arr.len(), 10);
    }

    #[test]
    fn test_generate_sparse_array() {
        let data = generate_sparse_array(10);
        let arr = data.as_array().unwrap();
        assert_eq!(arr.len(), 10);

        // Check that objects have varying numbers of fields
        let sizes: Vec<usize> = arr
            .iter()
            .filter_map(|v| v.as_object().map(IndexMap::len))
            .collect();
        assert!(sizes.iter().min() != sizes.iter().max(), "Objects should have varying field counts");
    }

    #[test]
    fn test_value_to_json() {
        let data = generate_api_response(2);
        let json = value_to_json(&data);
        assert!(json.starts_with('['));
        assert!(json.contains("\"id\":"));
        assert!(json.contains("\"name\":"));
    }
}
