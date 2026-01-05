//! Core library for token-efficient data format conversion.
//!
//! This crate provides the core functionality for llm-fmt:
//! - Parsing various input formats (JSON, YAML, XML, CSV)
//! - Encoding to token-efficient output formats (TOON, JSON, YAML, TSV)
//! - Filtering and transforming data structures
//! - Analysis and format recommendation
//! - Pipeline orchestration

pub mod analyze;
pub mod detect;
pub mod encoders;
pub mod error;
pub mod filters;
pub mod parsers;
pub mod pipeline;
pub mod tokens;
pub mod value;

pub use analyze::{analyze, format_report, report_to_json, AnalysisReport, FormatAnalysis};
pub use detect::{detect, detect_data_shape, select_format, DataShape};
pub use error::{Error, Result};
pub use pipeline::{Pipeline, PipelineBuilder};
pub use tokens::{calculate_savings, estimate_tokens};
pub use value::Value;
