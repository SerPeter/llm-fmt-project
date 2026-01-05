//! Python bindings for llm-fmt-core.
//!
//! This module exposes the Rust llm-fmt-core library to Python via `PyO3`.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use llm_fmt_core::{
    filters::{IncludeFilter, MaxDepthFilter},
    parsers::{CsvParser, JsonParser, XmlParser, YamlParser},
    PipelineBuilder,
};

/// Convert input data to a token-efficient format.
///
/// Args:
///     input: Input data as bytes or string.
///     format: Output format ("toon", "json", "yaml", "tsv", "csv"). Default: "toon".
///     `input_format`: Input format ("json", "yaml", "xml", "csv", "tsv", "auto"). Default: "auto".
///     `max_depth`: Maximum depth to traverse. Default: None (unlimited).
///     `sort_keys`: Sort object keys alphabetically. Default: False.
///     `include`: Path expression to extract (e.g., "users[*].name"). Default: None.
///
/// Returns:
///     Formatted output as string.
///
/// Raises:
///     `ValueError`: If parsing or encoding fails.
#[pyfunction]
#[pyo3(signature = (input, /, format = "toon", input_format = "auto", max_depth = None, sort_keys = false, include = None))]
fn convert(
    py: Python<'_>,
    input: &[u8],
    format: &str,
    input_format: &str,
    max_depth: Option<usize>,
    sort_keys: bool,
    include: Option<&str>,
) -> PyResult<String> {
    py.detach(|| {
        let mut builder = PipelineBuilder::new();

        // Set parser based on input format
        match input_format.to_lowercase().as_str() {
            "json" => builder = builder.with_parser(JsonParser),
            "yaml" | "yml" => builder = builder.with_parser(YamlParser),
            "xml" => builder = builder.with_parser(XmlParser),
            "csv" => builder = builder.with_parser(CsvParser::new()),
            "tsv" => builder = builder.with_parser(CsvParser::tsv()),
            "auto" => builder = builder.with_auto_parser(None, Some(input)),
            _ => {
                return Err(PyValueError::new_err(format!(
                    "Unsupported input format: {input_format}"
                )));
            }
        }

        // Set encoder
        builder = builder
            .with_format(format, sort_keys)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;

        // Add filters
        if let Some(depth) = max_depth {
            let filter = MaxDepthFilter::new(depth)
                .map_err(|e| PyValueError::new_err(e.to_string()))?;
            builder = builder.add_filter(filter);
        }

        if let Some(expr) = include {
            let filter = IncludeFilter::new(expr)
                .map_err(|e| PyValueError::new_err(e.to_string()))?;
            builder = builder.add_filter(filter);
        }

        // Build and run
        let pipeline = builder
            .build()
            .map_err(|e| PyValueError::new_err(e.to_string()))?;

        pipeline
            .run(input)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    })
}

/// Check if the Rust native module is available.
///
/// Returns:
///     True (always, since this is the Rust module).
#[pyfunction]
const fn is_available() -> bool {
    true
}

/// Get the version of the native module.
#[pyfunction]
const fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// Python module definition.
#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(convert, m)?)?;
    m.add_function(wrap_pyfunction!(is_available, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    Ok(())
}
