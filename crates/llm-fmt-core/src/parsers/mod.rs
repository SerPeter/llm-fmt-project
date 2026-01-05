//! Input parsers for various formats.
//!
//! This module provides parsers for JSON, YAML, XML, and CSV input formats.

mod csv;
mod json;
mod xml;
mod yaml;

pub use csv::CsvParser;
pub use json::JsonParser;
pub use xml::XmlParser;
pub use yaml::YamlParser;

use crate::{Result, Value};

/// Trait for input parsers.
pub trait Parser: Send + Sync {
    /// Parse input bytes into a [`Value`].
    ///
    /// # Errors
    ///
    /// Returns an error if parsing fails.
    fn parse(&self, input: &[u8]) -> Result<Value>;
}

/// Detect the appropriate parser based on filename extension or content.
///
/// # Arguments
///
/// * `filename` - Optional filename for extension-based detection
/// * `content` - Optional content for magic-byte detection
#[must_use]
pub fn detect_parser(filename: Option<&str>, content: Option<&[u8]>) -> Box<dyn Parser> {
    // Try filename extension first
    if let Some(name) = filename {
        if let Some(ext) = name.rsplit('.').next() {
            match ext.to_lowercase().as_str() {
                "json" | "jsonl" => return Box::new(JsonParser),
                "yaml" | "yml" => return Box::new(YamlParser),
                "xml" => return Box::new(XmlParser),
                "csv" => return Box::new(CsvParser::new()),
                "tsv" => return Box::new(CsvParser::tsv()),
                _ => {}
            }
        }
    }

    // Try content detection
    if let Some(bytes) = content {
        if let Ok(text) = std::str::from_utf8(bytes) {
            let trimmed = text.trim_start();
            if trimmed.starts_with('{') || trimmed.starts_with('[') {
                return Box::new(JsonParser);
            }
            if trimmed.starts_with("<?xml") || trimmed.starts_with('<') {
                return Box::new(XmlParser);
            }
        }
    }

    // Default to YAML (superset of JSON)
    Box::new(YamlParser)
}
