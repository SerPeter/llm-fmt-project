//! Analysis mode for comparing token efficiency across formats.
//!
//! This module provides functionality to analyze data and compare
//! token counts across different output formats, recommending the
//! optimal format for token efficiency.

use crate::detect::{detect, DataShape};
use crate::encoders::{CsvEncoder, Encoder, JsonEncoder, ToonEncoder, TsvEncoder, YamlEncoder};
use crate::tokens::{calculate_savings, estimate_tokens};
use crate::Value;

/// Token analysis for a single output format.
#[derive(Debug, Clone)]
pub struct FormatAnalysis {
    /// Format name (e.g., "TOON", "Compact JSON", "YAML").
    pub name: String,
    /// Estimated token count.
    pub tokens: usize,
    /// Savings percentage compared to baseline (pretty JSON).
    pub savings_percent: f64,
    /// Whether this format is recommended.
    pub recommended: bool,
    /// The encoded output (for inspection).
    pub output: String,
}

/// Complete analysis report comparing formats.
#[derive(Debug, Clone)]
pub struct AnalysisReport {
    /// Token count for baseline (pretty JSON).
    pub original_tokens: usize,
    /// Analysis for each format, sorted by token count.
    pub formats: Vec<FormatAnalysis>,
    /// Detected data shape.
    pub data_shape: DataShape,
    /// Recommended format name.
    pub recommendation: String,
    /// Reason for recommendation.
    pub recommendation_reason: String,
    /// Whether token counts are estimated (true) or exact (false).
    pub is_estimated: bool,
}

impl AnalysisReport {
    /// Get the best (lowest token count) format that's not the baseline.
    #[must_use]
    pub fn best_format(&self) -> Option<&FormatAnalysis> {
        self.formats.iter().find(|f| f.recommended)
    }

    /// Get the tokens saved by using the recommended format.
    #[must_use]
    pub fn tokens_saved(&self) -> usize {
        self.best_format()
            .map(|f| self.original_tokens.saturating_sub(f.tokens))
            .unwrap_or(0)
    }
}

/// Analyze data and compare format efficiency.
///
/// Generates output in all supported formats and compares token counts.
#[must_use]
pub fn analyze(value: &Value) -> AnalysisReport {
    // Generate baseline (pretty JSON with indentation)
    let pretty_json = generate_pretty_json(value);
    let baseline_tokens = estimate_tokens(&pretty_json);

    // Generate all format outputs
    let mut formats = Vec::new();

    // Pretty JSON (baseline)
    formats.push(FormatAnalysis {
        name: "JSON (pretty)".to_string(),
        tokens: baseline_tokens,
        savings_percent: 0.0,
        recommended: false,
        output: pretty_json,
    });

    // Compact JSON
    if let Ok(output) = JsonEncoder::new(false).encode(value) {
        let tokens = estimate_tokens(&output);
        formats.push(FormatAnalysis {
            name: "Compact JSON".to_string(),
            tokens,
            savings_percent: calculate_savings(baseline_tokens, tokens),
            recommended: false,
            output,
        });
    }

    // YAML
    if let Ok(output) = YamlEncoder::new().encode(value) {
        let tokens = estimate_tokens(&output);
        formats.push(FormatAnalysis {
            name: "YAML".to_string(),
            tokens,
            savings_percent: calculate_savings(baseline_tokens, tokens),
            recommended: false,
            output,
        });
    }

    // TOON
    if let Ok(output) = ToonEncoder::new().encode(value) {
        let tokens = estimate_tokens(&output);
        formats.push(FormatAnalysis {
            name: "TOON".to_string(),
            tokens,
            savings_percent: calculate_savings(baseline_tokens, tokens),
            recommended: false,
            output,
        });
    }

    // TSV (only for arrays)
    if value.is_array() {
        if let Ok(output) = TsvEncoder::new().encode(value) {
            let tokens = estimate_tokens(&output);
            formats.push(FormatAnalysis {
                name: "TSV".to_string(),
                tokens,
                savings_percent: calculate_savings(baseline_tokens, tokens),
                recommended: false,
                output,
            });
        }
    }

    // CSV (only for arrays)
    if value.is_array() {
        if let Ok(output) = CsvEncoder::new().encode(value) {
            let tokens = estimate_tokens(&output);
            formats.push(FormatAnalysis {
                name: "CSV".to_string(),
                tokens,
                savings_percent: calculate_savings(baseline_tokens, tokens),
                recommended: false,
                output,
            });
        }
    }

    // Detect data shape
    let data_shape = detect(value);

    // Determine recommendation
    let (recommendation, reason) = recommend_format(&data_shape, &formats);

    // Mark recommended format
    for fmt in &mut formats {
        fmt.recommended = fmt.name == recommendation;
    }

    // Sort by token count
    formats.sort_by_key(|f| f.tokens);

    AnalysisReport {
        original_tokens: baseline_tokens,
        formats,
        data_shape,
        recommendation,
        recommendation_reason: reason,
        is_estimated: true, // Always estimated until we add tiktoken
    }
}

/// Generate pretty-printed JSON for baseline comparison.
fn generate_pretty_json(value: &Value) -> String {
    // Use serde_json for pretty printing
    let json_value = value_to_serde_json(value);
    serde_json::to_string_pretty(&json_value).unwrap_or_else(|_| "{}".to_string())
}

/// Convert our Value to serde_json::Value for pretty printing.
fn value_to_serde_json(value: &Value) -> serde_json::Value {
    match value {
        Value::Null => serde_json::Value::Null,
        Value::Bool(b) => serde_json::Value::Bool(*b),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                serde_json::Value::Number(i.into())
            } else if let Some(u) = n.as_u64() {
                serde_json::Value::Number(u.into())
            } else {
                serde_json::Number::from_f64(n.as_f64())
                    .map(serde_json::Value::Number)
                    .unwrap_or(serde_json::Value::Null)
            }
        }
        Value::String(s) => serde_json::Value::String(s.clone()),
        Value::Array(arr) => {
            serde_json::Value::Array(arr.iter().map(value_to_serde_json).collect())
        }
        Value::Object(obj) => {
            let map: serde_json::Map<String, serde_json::Value> = obj
                .iter()
                .map(|(k, v)| (k.clone(), value_to_serde_json(v)))
                .collect();
            serde_json::Value::Object(map)
        }
    }
}

/// Determine best format based on data shape.
fn recommend_format(shape: &DataShape, formats: &[FormatAnalysis]) -> (String, String) {
    // TOON is best for uniform arrays
    if shape.is_uniform_array && shape.array_length > 1 {
        if formats.iter().any(|f| f.name == "TOON") {
            return (
                "TOON".to_string(),
                format!(
                    "Uniform array of {} objects with {} fields",
                    shape.array_length, shape.field_count
                ),
            );
        }
    }

    // YAML is good for shallow, mostly primitive structures
    if shape.max_depth <= 2 && shape.is_mostly_primitives {
        if formats.iter().any(|f| f.name == "YAML") {
            return (
                "YAML".to_string(),
                "Shallow structure with mostly primitive values".to_string(),
            );
        }
    }

    // Default: pick lowest token count that's not the baseline
    let non_baseline: Vec<&FormatAnalysis> = formats
        .iter()
        .filter(|f| f.name != "JSON (pretty)")
        .collect();

    if let Some(best) = non_baseline.iter().min_by_key(|f| f.tokens) {
        return (
            best.name.clone(),
            format!("Lowest token count ({} tokens)", best.tokens),
        );
    }

    ("Compact JSON".to_string(), "Default efficient format".to_string())
}

/// Format analysis report for terminal output.
#[must_use]
pub fn format_report(report: &AnalysisReport) -> String {
    let mut lines = Vec::new();

    // Header
    let estimation_note = if report.is_estimated { " (estimated)" } else { "" };
    lines.push(format!("Token Analysis{estimation_note}"));
    lines.push(String::new());

    // Table header
    lines.push(format!("{:<18} {:>10} {:>10}   ", "Format", "Tokens", "Savings"));
    lines.push("-".repeat(50));

    // Format rows
    for fmt in &report.formats {
        let savings = if fmt.savings_percent == 0.0 {
            "baseline".to_string()
        } else {
            format!("{:+.0}%", fmt.savings_percent)
        };

        let marker = if fmt.recommended {
            " <- recommended"
        } else if fmt.name == "JSON (pretty)" {
            " (baseline)"
        } else {
            ""
        };

        lines.push(format!(
            "{:<18} {:>10} {:>10}   {}",
            fmt.name,
            format_number(fmt.tokens),
            savings,
            marker
        ));
    }

    lines.push(String::new());

    // Data shape
    lines.push(format!("Data shape: {}", report.data_shape.description));

    // Recommendation
    if let Some(best) = report.best_format() {
        if best.name != "JSON (pretty)" {
            let tokens_saved = report.original_tokens.saturating_sub(best.tokens);
            lines.push(format!(
                "Recommendation: {} saves {} tokens ({:.0}%) per request",
                best.name,
                format_number(tokens_saved),
                best.savings_percent
            ));

            // Usage hint
            let fmt_arg = match best.name.as_str() {
                "TOON" => "toon",
                "Compact JSON" => "json",
                "YAML" => "yaml",
                "TSV" => "tsv",
                "CSV" => "csv",
                _ => "json",
            };
            lines.push(String::new());
            lines.push(format!("Use: llm-fmt <input> --format {fmt_arg}"));
        }
    }

    lines.join("\n")
}

/// Format a number with thousand separators.
fn format_number(n: usize) -> String {
    let s = n.to_string();
    let mut result = String::new();
    for (i, c) in s.chars().rev().enumerate() {
        if i > 0 && i % 3 == 0 {
            result.insert(0, ',');
        }
        result.insert(0, c);
    }
    result
}

/// Convert analysis report to a serializable structure for JSON output.
#[must_use]
pub fn report_to_json(report: &AnalysisReport) -> serde_json::Value {
    serde_json::json!({
        "original_tokens": report.original_tokens,
        "is_estimated": report.is_estimated,
        "formats": report.formats.iter().map(|f| {
            serde_json::json!({
                "name": f.name,
                "tokens": f.tokens,
                "savings_percent": f.savings_percent,
                "recommended": f.recommended,
            })
        }).collect::<Vec<_>>(),
        "data_shape": {
            "is_array": report.data_shape.is_array,
            "is_uniform_array": report.data_shape.is_uniform_array,
            "array_length": report.data_shape.array_length,
            "field_count": report.data_shape.field_count,
            "max_depth": report.data_shape.max_depth,
            "description": report.data_shape.description,
            "sample_keys": report.data_shape.sample_keys,
        },
        "recommendation": report.recommendation,
        "recommendation_reason": report.recommendation_reason,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use indexmap::IndexMap;

    fn make_uniform_array() -> Value {
        Value::Array(vec![
            {
                let mut obj = IndexMap::new();
                obj.insert("id".to_string(), Value::from(1));
                obj.insert("name".to_string(), Value::from("Alice"));
                Value::Object(obj)
            },
            {
                let mut obj = IndexMap::new();
                obj.insert("id".to_string(), Value::from(2));
                obj.insert("name".to_string(), Value::from("Bob"));
                Value::Object(obj)
            },
        ])
    }

    fn make_flat_object() -> Value {
        let mut obj = IndexMap::new();
        obj.insert("host".to_string(), Value::from("localhost"));
        obj.insert("port".to_string(), Value::from(5432));
        Value::Object(obj)
    }

    #[test]
    fn test_analyze_uniform_array() {
        let data = make_uniform_array();
        let report = analyze(&data);

        assert_eq!(report.recommendation, "TOON");
        assert!(report.data_shape.is_uniform_array);
        assert!(report.formats.iter().any(|f| f.name == "TOON" && f.recommended));
    }

    #[test]
    fn test_analyze_flat_object() {
        let data = make_flat_object();
        let report = analyze(&data);

        assert_eq!(report.recommendation, "YAML");
        assert!(report.data_shape.is_mostly_primitives);
    }

    #[test]
    fn test_format_report() {
        let data = make_uniform_array();
        let report = analyze(&data);
        let output = format_report(&report);

        assert!(output.contains("Token Analysis"));
        assert!(output.contains("Format"));
        assert!(output.contains("Tokens"));
        assert!(output.contains("recommended"));
    }

    #[test]
    fn test_report_to_json() {
        let data = make_uniform_array();
        let report = analyze(&data);
        let json = report_to_json(&report);

        assert!(json.get("original_tokens").is_some());
        assert!(json.get("formats").is_some());
        assert!(json.get("recommendation").is_some());
    }

    #[test]
    fn test_format_number() {
        assert_eq!(format_number(123), "123");
        assert_eq!(format_number(1234), "1,234");
        assert_eq!(format_number(1234567), "1,234,567");
    }

    #[test]
    fn test_tokens_saved() {
        let data = make_uniform_array();
        let report = analyze(&data);

        // TOON should save tokens compared to pretty JSON
        assert!(report.tokens_saved() > 0);
    }
}
