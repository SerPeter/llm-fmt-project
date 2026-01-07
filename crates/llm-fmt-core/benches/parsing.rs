//! Parsing benchmarks for all input formats.
//!
//! Measures parsing performance across different data shapes and sizes.

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use llm_fmt_core::benchdata::{
    generate_api_response, generate_nested_config, generate_tabular, value_to_csv, value_to_json,
    value_to_xml, value_to_yaml,
};
use llm_fmt_core::parsers::{CsvParser, JsonParser, Parser, XmlParser, YamlParser};

/// Benchmark JSON parsing at various data sizes.
fn bench_json_parsing(c: &mut Criterion) {
    let mut group = c.benchmark_group("json_parse");

    for size in [100, 1000, 10000] {
        let data = generate_api_response(size);
        let json = value_to_json(&data);
        let bytes = json.as_bytes();

        group.throughput(Throughput::Bytes(bytes.len() as u64));
        group.bench_with_input(
            BenchmarkId::new("api_response", size),
            &bytes,
            |b, bytes| {
                let parser = JsonParser;
                b.iter(|| parser.parse(bytes));
            },
        );
    }

    // Nested config
    for depth in [5, 10, 20] {
        let data = generate_nested_config(depth);
        let json = value_to_json(&data);
        let bytes = json.as_bytes();

        group.throughput(Throughput::Bytes(bytes.len() as u64));
        group.bench_with_input(
            BenchmarkId::new("nested_config", depth),
            &bytes,
            |b, bytes| {
                let parser = JsonParser;
                b.iter(|| parser.parse(bytes));
            },
        );
    }

    group.finish();
}

/// Benchmark YAML parsing at various data sizes.
fn bench_yaml_parsing(c: &mut Criterion) {
    let mut group = c.benchmark_group("yaml_parse");

    for size in [100, 1000, 10000] {
        let data = generate_api_response(size);
        let yaml = value_to_yaml(&data);
        let bytes = yaml.as_bytes();

        group.throughput(Throughput::Bytes(bytes.len() as u64));
        group.bench_with_input(
            BenchmarkId::new("api_response", size),
            &bytes,
            |b, bytes| {
                let parser = YamlParser;
                b.iter(|| parser.parse(bytes));
            },
        );
    }

    // Nested config
    for depth in [5, 10, 20] {
        let data = generate_nested_config(depth);
        let yaml = value_to_yaml(&data);
        let bytes = yaml.as_bytes();

        group.throughput(Throughput::Bytes(bytes.len() as u64));
        group.bench_with_input(
            BenchmarkId::new("nested_config", depth),
            &bytes,
            |b, bytes| {
                let parser = YamlParser;
                b.iter(|| parser.parse(bytes));
            },
        );
    }

    group.finish();
}

/// Benchmark XML parsing at various data sizes.
fn bench_xml_parsing(c: &mut Criterion) {
    let mut group = c.benchmark_group("xml_parse");

    for size in [100, 1000, 10000] {
        let data = generate_api_response(size);
        let xml = value_to_xml(&data, "users");
        let bytes = xml.as_bytes();

        group.throughput(Throughput::Bytes(bytes.len() as u64));
        group.bench_with_input(
            BenchmarkId::new("api_response", size),
            &bytes,
            |b, bytes| {
                let parser = XmlParser;
                b.iter(|| parser.parse(bytes));
            },
        );
    }

    // Nested config
    for depth in [5, 10, 20] {
        let data = generate_nested_config(depth);
        let xml = value_to_xml(&data, "config");
        let bytes = xml.as_bytes();

        group.throughput(Throughput::Bytes(bytes.len() as u64));
        group.bench_with_input(
            BenchmarkId::new("nested_config", depth),
            &bytes,
            |b, bytes| {
                let parser = XmlParser;
                b.iter(|| parser.parse(bytes));
            },
        );
    }

    group.finish();
}

/// Benchmark CSV parsing at various data sizes.
fn bench_csv_parsing(c: &mut Criterion) {
    let mut group = c.benchmark_group("csv_parse");

    for size in [100, 1000, 10000] {
        let data = generate_tabular(size);
        let csv = value_to_csv(&data).unwrap_or_default();
        let bytes = csv.as_bytes();

        group.throughput(Throughput::Bytes(bytes.len() as u64));
        group.bench_with_input(BenchmarkId::new("tabular", size), &bytes, |b, bytes| {
            let parser = CsvParser::new();
            b.iter(|| parser.parse(bytes));
        });
    }

    // API response as CSV
    for size in [100, 1000, 10000] {
        let data = generate_api_response(size);
        let csv = value_to_csv(&data).unwrap_or_default();
        let bytes = csv.as_bytes();

        group.throughput(Throughput::Bytes(bytes.len() as u64));
        group.bench_with_input(
            BenchmarkId::new("api_response", size),
            &bytes,
            |b, bytes| {
                let parser = CsvParser::new();
                b.iter(|| parser.parse(bytes));
            },
        );
    }

    group.finish();
}

/// Compare all parsers on similar data.
fn bench_parser_comparison(c: &mut Criterion) {
    let mut group = c.benchmark_group("parser_comparison");

    // Use medium-sized API response for comparison
    let data = generate_api_response(1000);

    // JSON
    {
        let json = value_to_json(&data);
        let bytes = json.as_bytes().to_vec();
        group.bench_with_input(
            BenchmarkId::new("json", "1k_objects"),
            &bytes,
            |b, bytes| {
                let parser = JsonParser;
                b.iter(|| parser.parse(bytes));
            },
        );
    }

    // YAML
    {
        let yaml = value_to_yaml(&data);
        let bytes = yaml.as_bytes().to_vec();
        group.bench_with_input(
            BenchmarkId::new("yaml", "1k_objects"),
            &bytes,
            |b, bytes| {
                let parser = YamlParser;
                b.iter(|| parser.parse(bytes));
            },
        );
    }

    // XML
    {
        let xml = value_to_xml(&data, "users");
        let bytes = xml.as_bytes().to_vec();
        group.bench_with_input(BenchmarkId::new("xml", "1k_objects"), &bytes, |b, bytes| {
            let parser = XmlParser;
            b.iter(|| parser.parse(bytes));
        });
    }

    // CSV
    {
        let csv = value_to_csv(&data).unwrap_or_default();
        let bytes = csv.as_bytes().to_vec();
        group.bench_with_input(BenchmarkId::new("csv", "1k_objects"), &bytes, |b, bytes| {
            let parser = CsvParser::new();
            b.iter(|| parser.parse(bytes));
        });
    }

    group.finish();
}

criterion_group!(
    benches,
    bench_json_parsing,
    bench_yaml_parsing,
    bench_xml_parsing,
    bench_csv_parsing,
    bench_parser_comparison,
);

criterion_main!(benches);
