//! Error types for llm-fmt-core.
//!
//! This module defines all error types used throughout the crate.

use thiserror::Error;

/// Result type alias using [`Error`].
pub type Result<T> = std::result::Result<T, Error>;

/// Main error type for llm-fmt-core operations.
#[derive(Debug, Error)]
pub enum Error {
    /// Error parsing input data.
    #[error("Parse error: {0}")]
    Parse(#[from] ParseError),

    /// Error encoding output.
    #[error("Encode error: {0}")]
    Encode(#[from] EncodeError),

    /// Error during filtering.
    #[error("Filter error: {0}")]
    Filter(#[from] FilterError),

    /// Error in pipeline configuration.
    #[error("Pipeline error: {0}")]
    Pipeline(String),
}

/// Errors that can occur during parsing.
#[derive(Debug, Error)]
pub enum ParseError {
    /// JSON parsing failed.
    #[error("JSON parse error: {0}")]
    Json(#[from] serde_json::Error),

    /// YAML parsing failed.
    #[error("YAML parse error: {0}")]
    Yaml(#[from] serde_yaml::Error),

    /// XML parsing failed.
    #[error("XML parse error: {0}")]
    Xml(#[from] quick_xml::DeError),

    /// CSV parsing failed.
    #[error("CSV parse error: {0}")]
    Csv(#[from] csv::Error),

    /// Input was not valid UTF-8.
    #[error("Invalid UTF-8: {0}")]
    Utf8(#[from] std::str::Utf8Error),

    /// Unknown or unsupported input format.
    #[error("Unknown format: {0}")]
    UnknownFormat(String),
}

/// Errors that can occur during encoding.
#[derive(Debug, Error)]
pub enum EncodeError {
    /// TOON encoding failed (e.g., non-uniform array).
    #[error("TOON encoding failed: {0}")]
    Toon(String),

    /// JSON encoding failed.
    #[error("JSON encoding failed: {0}")]
    Json(String),

    /// YAML encoding failed.
    #[error("YAML encoding failed: {0}")]
    Yaml(String),

    /// TSV encoding failed.
    #[error("TSV encoding failed: {0}")]
    Tsv(String),

    /// CSV encoding failed.
    #[error("CSV encoding failed: {0}")]
    Csv(String),

    /// Unknown output format.
    #[error("Unknown format: {0}")]
    UnknownFormat(String),
}

/// Errors that can occur during filtering.
#[derive(Debug, Error)]
pub enum FilterError {
    /// Invalid filter expression.
    #[error("Invalid filter expression: {0}")]
    InvalidExpression(String),

    /// Filter path not found in data.
    #[error("Path not found: {0}")]
    PathNotFound(String),

    /// `JMESPath` evaluation error.
    #[error("JMESPath error: {0}")]
    JmesPath(String),

    /// Invalid max depth value.
    #[error("Invalid max depth: {0}")]
    InvalidMaxDepth(String),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_display() {
        let err = Error::Pipeline("parser not set".into());
        assert_eq!(err.to_string(), "Pipeline error: parser not set");

        let err = Error::Parse(ParseError::UnknownFormat("xyz".into()));
        assert_eq!(err.to_string(), "Parse error: Unknown format: xyz");
    }
}
