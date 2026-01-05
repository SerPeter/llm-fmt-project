//! Core library for token-efficient data format conversion.
//!
//! This crate provides the core functionality for llm-fmt:
//! - Parsing various input formats (JSON, YAML, XML, CSV)
//! - Encoding to token-efficient output formats (TOON, JSON, YAML, TSV)
//! - Filtering and transforming data structures
//! - Pipeline orchestration

pub mod encoders;
pub mod error;
pub mod filters;
pub mod parsers;
pub mod pipeline;
pub mod value;

pub use error::{Error, Result};
pub use pipeline::{Pipeline, PipelineBuilder};
pub use value::Value;
