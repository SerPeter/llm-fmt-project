//! End-to-end pipeline benchmarks.
//!
//! Measures full conversion pipelines: parse -> filter -> encode.

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use llm_fmt_core::benchdata::{
    generate_api_response, generate_nested_config, generate_tabular, value_to_json, value_to_yaml,
};
use llm_fmt_core::filters::MaxDepthFilter;
use llm_fmt_core::parsers::JsonParser;
use llm_fmt_core::PipelineBuilder;

/// Benchmark JSON -> TOON conversion pipeline.
fn bench_json_to_toon(c: &mut Criterion) {
    let mut group = c.benchmark_group("pipeline_json_to_toon");

    for size in [100, 1000, 10000] {
        let data = generate_api_response(size);
        let json = value_to_json(&data);
        let bytes = json.as_bytes().to_vec();

        group.throughput(Throughput::Bytes(bytes.len() as u64));
        group.bench_with_input(
            BenchmarkId::new("api_response", size),
            &bytes,
            |b, bytes| {
                let pipeline = PipelineBuilder::new()
                    .with_parser(JsonParser)
                    .with_format("toon", false)
                    .unwrap()
                    .build()
                    .unwrap();
                b.iter(|| pipeline.run(bytes));
            },
        );
    }

    group.finish();
}

/// Benchmark JSON -> YAML conversion pipeline.
fn bench_json_to_yaml(c: &mut Criterion) {
    let mut group = c.benchmark_group("pipeline_json_to_yaml");

    for size in [100, 1000, 10000] {
        let data = generate_api_response(size);
        let json = value_to_json(&data);
        let bytes = json.as_bytes().to_vec();

        group.throughput(Throughput::Bytes(bytes.len() as u64));
        group.bench_with_input(
            BenchmarkId::new("api_response", size),
            &bytes,
            |b, bytes| {
                let pipeline = PipelineBuilder::new()
                    .with_parser(JsonParser)
                    .with_format("yaml", false)
                    .unwrap()
                    .build()
                    .unwrap();
                b.iter(|| pipeline.run(bytes));
            },
        );
    }

    group.finish();
}

/// Benchmark JSON -> TSV conversion pipeline.
fn bench_json_to_tsv(c: &mut Criterion) {
    let mut group = c.benchmark_group("pipeline_json_to_tsv");

    for size in [100, 1000, 10000] {
        let data = generate_tabular(size);
        let json = value_to_json(&data);
        let bytes = json.as_bytes().to_vec();

        group.throughput(Throughput::Bytes(bytes.len() as u64));
        group.bench_with_input(BenchmarkId::new("tabular", size), &bytes, |b, bytes| {
            let pipeline = PipelineBuilder::new()
                .with_parser(JsonParser)
                .with_format("tsv", false)
                .unwrap()
                .build()
                .unwrap();
            b.iter(|| pipeline.run(bytes));
        });
    }

    group.finish();
}

/// Benchmark pipeline with max-depth filter.
fn bench_pipeline_with_filter(c: &mut Criterion) {
    let mut group = c.benchmark_group("pipeline_with_filter");

    // Use nested config to test depth filtering
    for depth in [10, 20] {
        let data = generate_nested_config(depth);
        let json = value_to_json(&data);
        let bytes = json.as_bytes().to_vec();

        // Without filter
        group.bench_with_input(BenchmarkId::new("no_filter", depth), &bytes, |b, bytes| {
            let pipeline = PipelineBuilder::new()
                .with_parser(JsonParser)
                .with_format("json", false)
                .unwrap()
                .build()
                .unwrap();
            b.iter(|| pipeline.run(bytes));
        });

        // With max-depth filter (depth 3)
        group.bench_with_input(
            BenchmarkId::new("max_depth_3", depth),
            &bytes,
            |b, bytes| {
                let pipeline = PipelineBuilder::new()
                    .with_parser(JsonParser)
                    .add_filter(MaxDepthFilter::new(3).unwrap())
                    .with_format("json", false)
                    .unwrap()
                    .build()
                    .unwrap();
                b.iter(|| pipeline.run(bytes));
            },
        );
    }

    group.finish();
}

/// Compare all output formats for the same input.
fn bench_format_comparison(c: &mut Criterion) {
    let mut group = c.benchmark_group("format_comparison");

    let data = generate_api_response(1000);
    let json = value_to_json(&data);
    let bytes = json.as_bytes().to_vec();

    for format in ["toon", "json", "yaml", "tsv", "csv"] {
        group.bench_with_input(
            BenchmarkId::new(format, "1k_objects"),
            &bytes,
            |b, bytes| {
                let pipeline = PipelineBuilder::new()
                    .with_parser(JsonParser)
                    .with_format(format, false)
                    .unwrap()
                    .build()
                    .unwrap();
                b.iter(|| pipeline.run(bytes));
            },
        );
    }

    group.finish();
}

/// Benchmark YAML input to various outputs.
fn bench_yaml_input(c: &mut Criterion) {
    let mut group = c.benchmark_group("pipeline_yaml_input");

    let data = generate_api_response(1000);
    let yaml = value_to_yaml(&data);
    let bytes = yaml.as_bytes().to_vec();

    for format in ["toon", "json"] {
        group.bench_with_input(
            BenchmarkId::new(format!("yaml_to_{format}"), "1k_objects"),
            &bytes,
            |b, bytes| {
                let pipeline = PipelineBuilder::new()
                    .with_auto_parser(Some("input.yaml"), None)
                    .with_format(format, false)
                    .unwrap()
                    .build()
                    .unwrap();
                b.iter(|| pipeline.run(bytes));
            },
        );
    }

    group.finish();
}

criterion_group!(
    benches,
    bench_json_to_toon,
    bench_json_to_yaml,
    bench_json_to_tsv,
    bench_pipeline_with_filter,
    bench_format_comparison,
    bench_yaml_input,
);

criterion_main!(benches);
