//! Benchmark report generator.
//!
//! Generates a summary report with key metrics:
//! - Output tokens
//! - Token savings %
//! - Output size (bytes)
//! - Encoding time
//!
//! Usage:
//!   cargo run --release --bin benchreport

use std::time::{Duration, Instant};

use llm_fmt_core::benchdata::{generate_api_response, generate_nested_config, generate_tabular};
use llm_fmt_core::encoders::{
    CsvEncoder, Encoder, JsonEncoder, ToonEncoder, TsvEncoder, YamlEncoder,
};
use llm_fmt_core::tokens::{calculate_savings, estimate_tokens};
use llm_fmt_core::Value;

/// Number of iterations for timing measurements.
const TIMING_ITERATIONS: usize = 10;

fn main() {
    println!("# LLM-FMT Benchmark Report\n");
    println!("Measuring: Output tokens, Token savings %, Output size, Encoding time\n");

    // Benchmark uniform arrays (API response style)
    println!("## Uniform Arrays (API Response)\n");
    println!("| Size | Format | Tokens | Savings | Bytes | Time |");
    println!("|------|--------|--------|---------|-------|------|");

    for size in [100, 1000, 10000] {
        let data = generate_api_response(size);
        let input_json = serde_json::to_string(&value_to_serde(&data)).unwrap();
        let input_tokens = estimate_tokens(&input_json);

        for (format_name, encoder) in get_encoders() {
            let metrics = measure_encoding(&data, encoder.as_ref(), TIMING_ITERATIONS);
            let savings = calculate_savings(input_tokens, metrics.tokens);

            println!(
                "| {:>4} | {:>6} | {:>6} | {:>6.1}% | {:>5} | {:>4} |",
                format_size(size),
                format_name,
                metrics.tokens,
                savings,
                format_bytes(metrics.bytes),
                format_duration(metrics.avg_time)
            );
        }
    }

    // Benchmark nested config
    println!("\n## Nested Config (Deep Structures)\n");
    println!("| Depth | Format | Tokens | Savings | Bytes | Time |");
    println!("|-------|--------|--------|---------|-------|------|");

    for depth in [5, 10, 20] {
        let data = generate_nested_config(depth);
        let input_json = serde_json::to_string(&value_to_serde(&data)).unwrap();
        let input_tokens = estimate_tokens(&input_json);

        // Only JSON and YAML make sense for nested config
        for (format_name, encoder) in [
            (
                "json",
                Box::new(JsonEncoder::new(false)) as Box<dyn Encoder>,
            ),
            ("yaml", Box::new(YamlEncoder::new())),
        ] {
            let metrics = measure_encoding(&data, encoder.as_ref(), TIMING_ITERATIONS);
            let savings = calculate_savings(input_tokens, metrics.tokens);

            println!(
                "| {:>5} | {:>6} | {:>6} | {:>6.1}% | {:>5} | {:>4} |",
                depth,
                format_name,
                metrics.tokens,
                savings,
                format_bytes(metrics.bytes),
                format_duration(metrics.avg_time)
            );
        }
    }

    // Benchmark tabular data
    println!("\n## Tabular Data\n");
    println!("| Size | Format | Tokens | Savings | Bytes | Time |");
    println!("|------|--------|--------|---------|-------|------|");

    for size in [100, 1000, 10000] {
        let data = generate_tabular(size);
        let input_json = serde_json::to_string(&value_to_serde(&data)).unwrap();
        let input_tokens = estimate_tokens(&input_json);

        for (format_name, encoder) in get_encoders() {
            let metrics = measure_encoding(&data, encoder.as_ref(), TIMING_ITERATIONS);
            let savings = calculate_savings(input_tokens, metrics.tokens);

            println!(
                "| {:>4} | {:>6} | {:>6} | {:>6.1}% | {:>5} | {:>4} |",
                format_size(size),
                format_name,
                metrics.tokens,
                savings,
                format_bytes(metrics.bytes),
                format_duration(metrics.avg_time)
            );
        }
    }

    println!("\n## Summary\n");
    println!("- **Best for uniform arrays**: TOON/TSV (highest savings)");
    println!("- **Best for nested data**: YAML (readable, good savings)");
    println!("- **Fastest encoding**: JSON (minimal transformation)");
    println!("\nRun `cargo bench` for detailed timing analysis with Criterion.");
}

/// Get all encoders for benchmarking.
fn get_encoders() -> Vec<(&'static str, Box<dyn Encoder>)> {
    vec![
        ("toon", Box::new(ToonEncoder::new())),
        ("json", Box::new(JsonEncoder::new(false))),
        ("yaml", Box::new(YamlEncoder::new())),
        ("tsv", Box::new(TsvEncoder::new())),
        ("csv", Box::new(CsvEncoder::new())),
    ]
}

struct EncodingMetrics {
    tokens: usize,
    bytes: usize,
    avg_time: Duration,
}

/// Measure encoding performance.
fn measure_encoding(data: &Value, encoder: &dyn Encoder, iterations: usize) -> EncodingMetrics {
    // Warmup
    let _ = encoder.encode(data);

    // Measure time
    let start = Instant::now();
    let mut output = String::new();
    for _ in 0..iterations {
        output = encoder.encode(data).unwrap_or_default();
    }
    let elapsed = start.elapsed();

    EncodingMetrics {
        tokens: estimate_tokens(&output),
        bytes: output.len(),
        avg_time: elapsed / iterations as u32,
    }
}

/// Format size with K suffix.
fn format_size(size: usize) -> String {
    if size >= 1000 {
        format!("{}K", size / 1000)
    } else {
        format!("{size}")
    }
}

/// Format bytes with K/M suffix.
fn format_bytes(bytes: usize) -> String {
    if bytes >= 1_000_000 {
        format!("{:.1}M", bytes as f64 / 1_000_000.0)
    } else if bytes >= 1000 {
        format!("{}K", bytes / 1000)
    } else {
        format!("{bytes}B")
    }
}

/// Format duration in human-readable form.
fn format_duration(d: Duration) -> String {
    let micros = d.as_micros();
    if micros >= 1000 {
        format!("{}ms", micros / 1000)
    } else {
        format!("{micros}µs")
    }
}

/// Convert Value to serde_json::Value for baseline measurement.
fn value_to_serde(value: &Value) -> serde_json::Value {
    match value {
        Value::Null => serde_json::Value::Null,
        Value::Bool(b) => serde_json::Value::Bool(*b),
        Value::Number(n) => serde_json::json!(n.as_f64()),
        Value::String(s) => serde_json::Value::String(s.clone()),
        Value::Array(arr) => serde_json::Value::Array(arr.iter().map(value_to_serde).collect()),
        Value::Object(obj) => serde_json::Value::Object(
            obj.iter()
                .map(|(k, v)| (k.clone(), value_to_serde(v)))
                .collect(),
        ),
    }
}
