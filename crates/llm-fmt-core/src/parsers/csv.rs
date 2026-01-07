//! CSV parser implementation.

use crate::error::ParseError;
use crate::value::{Number, Value};
use crate::Result;

use super::Parser;

/// Parser for CSV input.
///
/// Converts CSV to a list of objects using the first row as headers.
#[derive(Debug, Clone)]
pub struct CsvParser {
    /// Field delimiter (default: comma).
    delimiter: u8,
    /// Whether the first row contains headers.
    has_header: bool,
}

impl Default for CsvParser {
    fn default() -> Self {
        Self {
            delimiter: b',',
            has_header: true,
        }
    }
}

impl CsvParser {
    /// Create a new CSV parser with default settings.
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Create a CSV parser with a custom delimiter.
    #[must_use]
    pub const fn with_delimiter(delimiter: u8) -> Self {
        Self {
            delimiter,
            has_header: true,
        }
    }

    /// Create a TSV parser (tab-separated values).
    #[must_use]
    pub const fn tsv() -> Self {
        Self::with_delimiter(b'\t')
    }

    /// Set whether the first row contains headers.
    #[must_use]
    pub const fn with_header(mut self, has_header: bool) -> Self {
        self.has_header = has_header;
        self
    }
}

impl Parser for CsvParser {
    fn parse(&self, input: &[u8]) -> Result<Value> {
        let mut reader = csv::ReaderBuilder::new()
            .delimiter(self.delimiter)
            .has_headers(self.has_header)
            .from_reader(input);

        if self.has_header {
            parse_with_headers(&mut reader)
        } else {
            parse_without_headers(&mut reader)
        }
    }
}

/// Parse CSV with headers into array of objects.
fn parse_with_headers(reader: &mut csv::Reader<&[u8]>) -> Result<Value> {
    let headers: Vec<String> = reader
        .headers()
        .map_err(ParseError::from)?
        .iter()
        .map(String::from)
        .collect();

    let mut rows = Vec::new();

    for result in reader.records() {
        let record = result.map_err(ParseError::from)?;
        let mut obj = indexmap::IndexMap::new();

        for (i, field) in record.iter().enumerate() {
            if let Some(header) = headers.get(i) {
                obj.insert(header.clone(), parse_field(field));
            }
        }

        rows.push(Value::Object(obj));
    }

    Ok(Value::Array(rows))
}

/// Parse CSV without headers into array of arrays.
fn parse_without_headers(reader: &mut csv::Reader<&[u8]>) -> Result<Value> {
    let mut rows = Vec::new();

    for result in reader.records() {
        let record = result.map_err(ParseError::from)?;
        let row: Vec<Value> = record.iter().map(parse_field).collect();
        rows.push(Value::Array(row));
    }

    Ok(Value::Array(rows))
}

/// Parse a single field, attempting type conversion.
fn parse_field(field: &str) -> Value {
    let trimmed = field.trim();

    if trimmed.is_empty() {
        return Value::Null;
    }

    // Try boolean
    if trimmed.eq_ignore_ascii_case("true") {
        return Value::Bool(true);
    }
    if trimmed.eq_ignore_ascii_case("false") {
        return Value::Bool(false);
    }

    // Try integer
    if let Ok(i) = trimmed.parse::<i64>() {
        return Value::Number(Number::Int(i));
    }

    // Try float
    if let Ok(f) = trimmed.parse::<f64>() {
        return Value::Number(Number::Float(f));
    }

    Value::String(field.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_with_headers() {
        let parser = CsvParser::new();
        let input = b"name,age,active\nAlice,30,true\nBob,25,false";
        let result = parser.parse(input).unwrap();

        let arr = result.as_array().unwrap();
        assert_eq!(arr.len(), 2);

        let first = &arr[0];
        assert_eq!(first.get("name").and_then(Value::as_str), Some("Alice"));
        assert_eq!(
            first.get("age").and_then(|v| v.as_number()?.as_i64()),
            Some(30)
        );
        assert_eq!(first.get("active").and_then(Value::as_bool), Some(true));
    }

    #[test]
    fn test_parse_tsv() {
        let parser = CsvParser::tsv();
        let input = b"name\tage\nAlice\t30\nBob\t25";
        let result = parser.parse(input).unwrap();

        let arr = result.as_array().unwrap();
        assert_eq!(arr.len(), 2);
        assert_eq!(arr[0].get("name").and_then(Value::as_str), Some("Alice"));
    }

    #[test]
    fn test_parse_without_headers() {
        let parser = CsvParser::new().with_header(false);
        let input = b"Alice,30\nBob,25";
        let result = parser.parse(input).unwrap();

        let arr = result.as_array().unwrap();
        assert_eq!(arr.len(), 2);

        let first = arr[0].as_array().unwrap();
        assert_eq!(first[0].as_str(), Some("Alice"));
    }

    #[test]
    fn test_parse_empty_fields() {
        let parser = CsvParser::new();
        let input = b"name,value\ntest,\n,empty";
        let result = parser.parse(input).unwrap();

        let arr = result.as_array().unwrap();
        assert!(arr[0].get("value").unwrap().is_null());
        assert!(arr[1].get("name").unwrap().is_null());
    }

    #[test]
    fn test_parse_quoted_fields() {
        let parser = CsvParser::new();
        let input = b"name,desc\ntest,\"has, comma\"\nother,\"has \"\"quotes\"\"\"";
        let result = parser.parse(input).unwrap();

        let arr = result.as_array().unwrap();
        assert_eq!(
            arr[0].get("desc").and_then(Value::as_str),
            Some("has, comma")
        );
    }
}
