//! XML parser implementation.

use crate::error::ParseError;
use crate::value::{Number, Value};
use crate::Result;

use super::Parser;

/// Parser for XML input.
///
/// Converts XML to a nested object structure similar to xmltodict in Python.
#[derive(Debug, Default, Clone, Copy)]
pub struct XmlParser;

impl Parser for XmlParser {
    fn parse(&self, input: &[u8]) -> Result<Value> {
        let text = std::str::from_utf8(input).map_err(ParseError::from)?;
        parse_xml_string(text).map_err(|e| ParseError::Xml(e).into())
    }
}

/// Parse XML string into Value.
fn parse_xml_string(xml: &str) -> std::result::Result<Value, quick_xml::DeError> {
    use quick_xml::events::Event;
    use quick_xml::Reader;

    let mut reader = Reader::from_str(xml);
    reader.config_mut().trim_text(true);

    let mut stack: Vec<(String, Value)> = Vec::new();

    loop {
        match reader.read_event() {
            Ok(Event::Start(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                stack.push((name, Value::Null));
            }
            Ok(Event::End(_)) => {
                if let Some((name, value)) = stack.pop() {
                    if let Some((_, parent)) = stack.last_mut() {
                        add_to_parent(parent, &name, value);
                    } else {
                        // Root element
                        let mut root = indexmap::IndexMap::new();
                        root.insert(name, value);
                        return Ok(Value::Object(root));
                    }
                }
            }
            Ok(Event::Empty(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if let Some((_, parent)) = stack.last_mut() {
                    add_to_parent(parent, &name, Value::Null);
                } else {
                    let mut root = indexmap::IndexMap::new();
                    root.insert(name, Value::Null);
                    return Ok(Value::Object(root));
                }
            }
            Ok(Event::Text(e)) => {
                let text = e.unescape().unwrap_or_default().trim().to_string();
                if !text.is_empty() {
                    if let Some((_, value)) = stack.last_mut() {
                        *value = parse_text_value(&text);
                    }
                }
            }
            Ok(Event::CData(e)) => {
                let text = String::from_utf8_lossy(&e).to_string();
                if let Some((_, value)) = stack.last_mut() {
                    *value = Value::String(text);
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(quick_xml::DeError::Custom(e.to_string())),
            _ => {}
        }
    }

    // If we get here with no root, return null
    Ok(Value::Null)
}

/// Add a child element to a parent value.
fn add_to_parent(parent: &mut Value, name: &str, child: Value) {
    match parent {
        Value::Null => {
            let mut obj = indexmap::IndexMap::new();
            obj.insert(name.to_string(), child);
            *parent = Value::Object(obj);
        }
        Value::Object(obj) => {
            if let Some(existing) = obj.get_mut(name) {
                // Convert to array if duplicate key
                if let Value::Array(arr) = existing {
                    arr.push(child);
                } else {
                    let prev = std::mem::replace(existing, Value::Null);
                    *existing = Value::Array(vec![prev, child]);
                }
            } else {
                obj.insert(name.to_string(), child);
            }
        }
        _ => {
            // Parent is a text value, wrap it
            let text = std::mem::replace(parent, Value::Null);
            let mut obj = indexmap::IndexMap::new();
            obj.insert("#text".to_string(), text);
            obj.insert(name.to_string(), child);
            *parent = Value::Object(obj);
        }
    }
}

/// Parse text content, attempting to convert to number/bool.
fn parse_text_value(text: &str) -> Value {
    // Try boolean
    if text.eq_ignore_ascii_case("true") {
        return Value::Bool(true);
    }
    if text.eq_ignore_ascii_case("false") {
        return Value::Bool(false);
    }

    // Try integer
    if let Ok(i) = text.parse::<i64>() {
        return Value::Number(Number::Int(i));
    }

    // Try float
    if let Ok(f) = text.parse::<f64>() {
        return Value::Number(Number::Float(f));
    }

    Value::String(text.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple_element() {
        let parser = XmlParser;
        let input = b"<root><name>Alice</name><age>30</age></root>";
        let result = parser.parse(input).unwrap();

        let root = result.get("root").unwrap();
        assert_eq!(root.get("name").and_then(Value::as_str), Some("Alice"));
        assert_eq!(
            root.get("age").and_then(|v| v.as_number()?.as_i64()),
            Some(30)
        );
    }

    #[test]
    fn test_parse_nested() {
        let parser = XmlParser;
        let input = b"<root><user><id>1</id></user></root>";
        let result = parser.parse(input).unwrap();

        let user = result.get("root").and_then(|r| r.get("user")).unwrap();
        assert_eq!(
            user.get("id").and_then(|v| v.as_number()?.as_i64()),
            Some(1)
        );
    }

    #[test]
    fn test_parse_repeated_elements() {
        let parser = XmlParser;
        let input = b"<root><item>1</item><item>2</item><item>3</item></root>";
        let result = parser.parse(input).unwrap();

        let items = result
            .get("root")
            .and_then(|r| r.get("item"))
            .and_then(Value::as_array)
            .unwrap();
        assert_eq!(items.len(), 3);
    }

    #[test]
    fn test_parse_empty_element() {
        let parser = XmlParser;
        let input = b"<root><empty/></root>";
        let result = parser.parse(input).unwrap();

        let empty = result.get("root").and_then(|r| r.get("empty")).unwrap();
        assert!(empty.is_null());
    }
}
