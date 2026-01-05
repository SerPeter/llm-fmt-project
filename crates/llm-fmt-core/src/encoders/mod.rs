//! Output encoders for various formats.
//!
//! This module provides encoders for TOON, JSON, YAML, TSV, and CSV output formats.

mod csv;
mod json;
mod toon;
mod tsv;
mod yaml;

pub use csv::CsvEncoder;
pub use json::JsonEncoder;
pub use toon::ToonEncoder;
pub use tsv::TsvEncoder;
pub use yaml::YamlEncoder;

use crate::{error::EncodeError, Result, Value};

/// Trait for output encoders.
pub trait Encoder: Send + Sync {
    /// Encode a [`Value`] to a string.
    ///
    /// # Errors
    ///
    /// Returns an error if encoding fails.
    fn encode(&self, value: &Value) -> Result<String>;
}

/// Get an encoder by format name.
///
/// # Arguments
///
/// * `format` - Format name (toon, json, yaml, tsv, csv)
/// * `sort_keys` - Whether to sort object keys (JSON only)
///
/// # Errors
///
/// Returns an error if the format is unknown.
pub fn get_encoder(format: &str, sort_keys: bool) -> Result<Box<dyn Encoder>> {
    match format.to_lowercase().as_str() {
        "toon" => Ok(Box::new(ToonEncoder::new())),
        "json" => Ok(Box::new(JsonEncoder::new(sort_keys))),
        "yaml" => Ok(Box::new(YamlEncoder::new())),
        "tsv" => Ok(Box::new(TsvEncoder::new())),
        "csv" => Ok(Box::new(CsvEncoder::new())),
        _ => Err(EncodeError::UnknownFormat(format.to_owned()).into()),
    }
}
