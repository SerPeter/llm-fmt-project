//! Python bindings for llm-fmt-core.
//!
//! This module exposes the Rust llm-fmt-core library to Python via `PyO3`.

#![allow(clippy::too_many_arguments)]
#![allow(clippy::needless_pass_by_value)]
#![allow(clippy::doc_link_with_quotes)]

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::IntoPyObjectExt;

use llm_fmt_core::{
    analyze as core_analyze, detect as core_detect,
    filters::{IncludeFilter, MaxDepthFilter, TruncationFilter, TruncationStrategy},
    format_report,
    parsers::{CsvParser, JsonParser, Parser, XmlParser, YamlParser},
    report_to_json, select_format as core_select_format, PipelineBuilder,
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
///     `max_items`: Maximum items per array. Default: None (unlimited).
///     `max_string_length`: Maximum length for string values. Default: None (unlimited).
///     `truncation_strategy`: Strategy for array truncation ("head", "tail", "sample", "balanced"). Default: "head".
///     `preserve`: Paths to preserve from truncation (e.g., ["$.id", "$.metadata"]). Default: None.
///
/// Returns:
///     Formatted output as string.
///
/// Raises:
///     `ValueError`: If parsing or encoding fails.
#[pyfunction]
#[pyo3(signature = (input, /, format = "toon", input_format = "auto", max_depth = None, sort_keys = false, include = None, max_items = None, max_string_length = None, truncation_strategy = "head", preserve = None))]
fn convert(
    py: Python<'_>,
    input: &[u8],
    format: &str,
    input_format: &str,
    max_depth: Option<usize>,
    sort_keys: bool,
    include: Option<&str>,
    max_items: Option<usize>,
    max_string_length: Option<usize>,
    truncation_strategy: &str,
    preserve: Option<Vec<String>>,
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
            let filter =
                MaxDepthFilter::new(depth).map_err(|e| PyValueError::new_err(e.to_string()))?;
            builder = builder.add_filter(filter);
        }

        if let Some(expr) = include {
            let filter =
                IncludeFilter::new(expr).map_err(|e| PyValueError::new_err(e.to_string()))?;
            builder = builder.add_filter(filter);
        }

        // Add truncation filter if any truncation options are set
        if max_items.is_some() || max_string_length.is_some() {
            let strategy = TruncationStrategy::from_str(truncation_strategy)
                .map_err(|e| PyValueError::new_err(e.to_string()))?;

            let mut filter = TruncationFilter::new().with_strategy(strategy);

            if let Some(items) = max_items {
                filter = filter.with_max_items(items);
            }

            if let Some(length) = max_string_length {
                filter = filter.with_max_string_length(length);
            }

            if let Some(ref paths) = preserve {
                let path_refs: Vec<&str> = paths.iter().map(String::as_str).collect();
                filter = filter.with_preserve_paths(&path_refs);
            }

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

/// Analyze input data and compare token efficiency across formats.
///
/// Args:
///     input: Input data as bytes.
///     input_format: Input format ("json", "yaml", "xml", "csv", "tsv", "auto"). Default: "auto".
///     output_json: If True, return JSON dict; if False, return formatted string. Default: False.
///
/// Returns:
///     Analysis report as formatted string or JSON dict.
///
/// Raises:
///     `ValueError`: If parsing fails.
#[pyfunction]
#[pyo3(signature = (input, /, input_format = "auto", output_json = false))]
fn analyze(
    py: Python<'_>,
    input: &[u8],
    input_format: &str,
    output_json: bool,
) -> PyResult<Py<PyAny>> {
    // Parse input
    let value = parse_input(input, input_format)?;

    // Run analysis
    let report = core_analyze(&value);

    if output_json {
        // Return as JSON dict
        let json_value = report_to_json(&report);
        let json_str = json_value.to_string();

        // Parse JSON string to Python dict
        let json_module = py.import("json")?;
        let loads = json_module.getattr("loads")?;
        let result = loads.call1((json_str,))?;
        Ok(result.into_py_any(py)?)
    } else {
        // Return formatted string
        let output = format_report(&report);
        Ok(output.into_py_any(py)?)
    }
}

/// Detect the shape of input data.
///
/// Args:
///     input: Input data as bytes.
///     input_format: Input format ("json", "yaml", "xml", "csv", "tsv", "auto"). Default: "auto".
///
/// Returns:
///     Dict with data shape information.
///
/// Raises:
///     `ValueError`: If parsing fails.
#[pyfunction]
#[pyo3(signature = (input, /, input_format = "auto"))]
fn detect_shape(py: Python<'_>, input: &[u8], input_format: &str) -> PyResult<Py<PyAny>> {
    // Parse input
    let value = parse_input(input, input_format)?;

    // Detect shape
    let shape = core_detect(&value);

    // Convert to Python dict
    let dict = PyDict::new(py);
    dict.set_item("is_array", shape.is_array)?;
    dict.set_item("is_uniform_array", shape.is_uniform_array)?;
    dict.set_item("array_length", shape.array_length)?;
    dict.set_item("field_count", shape.field_count)?;
    dict.set_item("max_depth", shape.max_depth)?;
    dict.set_item("is_mostly_primitives", shape.is_mostly_primitives)?;
    dict.set_item("description", shape.description)?;
    dict.set_item("sample_keys", shape.sample_keys)?;
    dict.into_py_any(py)
}

/// Select the optimal output format based on data shape.
///
/// Args:
///     input: Input data as bytes.
///     input_format: Input format ("json", "yaml", "xml", "csv", "tsv", "auto"). Default: "auto".
///
/// Returns:
///     Recommended format name ("toon", "yaml", or "json").
///
/// Raises:
///     `ValueError`: If parsing fails.
#[pyfunction]
#[pyo3(signature = (input, /, input_format = "auto"))]
fn select_format(_py: Python<'_>, input: &[u8], input_format: &str) -> PyResult<String> {
    // Parse input
    let value = parse_input(input, input_format)?;

    // Select format
    Ok(core_select_format(&value).to_string())
}

/// Helper function to parse input based on format.
fn parse_input(input: &[u8], input_format: &str) -> PyResult<llm_fmt_core::Value> {
    let parser: Box<dyn Parser> = match input_format.to_lowercase().as_str() {
        "json" => Box::new(JsonParser),
        "yaml" | "yml" => Box::new(YamlParser),
        "xml" => Box::new(XmlParser),
        "csv" => Box::new(CsvParser::new()),
        "tsv" => Box::new(CsvParser::tsv()),
        "auto" => {
            // Auto-detect based on content
            let content = std::str::from_utf8(input).unwrap_or("");
            let trimmed = content.trim();
            if trimmed.starts_with('{') || trimmed.starts_with('[') {
                Box::new(JsonParser)
            } else if trimmed.starts_with('<') {
                Box::new(XmlParser)
            } else if trimmed.contains(':') && !trimmed.contains(',') {
                Box::new(YamlParser)
            } else {
                Box::new(JsonParser)
            }
        }
        _ => {
            return Err(PyValueError::new_err(format!(
                "Unsupported input format: {input_format}"
            )));
        }
    };

    parser
        .parse(input)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Python module definition.
#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(convert, m)?)?;
    m.add_function(wrap_pyfunction!(is_available, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(analyze, m)?)?;
    m.add_function(wrap_pyfunction!(detect_shape, m)?)?;
    m.add_function(wrap_pyfunction!(select_format, m)?)?;
    Ok(())
}
