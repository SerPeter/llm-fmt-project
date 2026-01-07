//! Encoding benchmarks for all output formats.
//!
//! Measures encoding performance across different data shapes and sizes.

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use llm_fmt_core::benchdata::{
    generate_api_response, generate_mixed_types, generate_nested_config, generate_sparse_array,
    generate_tabular,
};
use llm_fmt_core::encoders::{
    CsvEncoder, Encoder, JsonEncoder, ToonEncoder, TsvEncoder, YamlEncoder,
};
use llm_fmt_core::Value;

/// Benchmark TOON encoding at various data sizes.
fn bench_toon_encoding(c: &mut Criterion) {
    let mut group = c.benchmark_group("toon_encode");

    // Uniform arrays (best case for TOON)
    for size in [100, 1000, 10000] {
        let data = generate_api_response(size);
        let byte_size = estimate_value_size(&data);
        group.throughput(Throughput::Bytes(byte_size as u64));

        group.bench_with_input(BenchmarkId::new("api_response", size), &data, |b, data| {
            let encoder = ToonEncoder::new();
            b.iter(|| encoder.encode(data));
        });
    }

    // Sparse arrays (challenging for TOON)
    for size in [100, 1000] {
        let data = generate_sparse_array(size);

        group.bench_with_input(BenchmarkId::new("sparse_array", size), &data, |b, data| {
            let encoder = ToonEncoder::new();
            b.iter(|| encoder.encode(data));
        });
    }

    group.finish();
}

/// Benchmark JSON encoding at various data sizes.
fn bench_json_encoding(c: &mut Criterion) {
    let mut group = c.benchmark_group("json_encode");

    for size in [100, 1000, 10000] {
        let data = generate_api_response(size);
        let byte_size = estimate_value_size(&data);
        group.throughput(Throughput::Bytes(byte_size as u64));

        group.bench_with_input(BenchmarkId::new("api_response", size), &data, |b, data| {
            let encoder = JsonEncoder::new(false);
            b.iter(|| encoder.encode(data));
        });
    }

    // Nested config (deep structures)
    for depth in [5, 10, 20] {
        let data = generate_nested_config(depth);

        group.bench_with_input(
            BenchmarkId::new("nested_config", depth),
            &data,
            |b, data| {
                let encoder = JsonEncoder::new(false);
                b.iter(|| encoder.encode(data));
            },
        );
    }

    group.finish();
}

/// Benchmark YAML encoding at various data sizes.
fn bench_yaml_encoding(c: &mut Criterion) {
    let mut group = c.benchmark_group("yaml_encode");

    for size in [100, 1000, 10000] {
        let data = generate_api_response(size);

        group.bench_with_input(BenchmarkId::new("api_response", size), &data, |b, data| {
            let encoder = YamlEncoder::new();
            b.iter(|| encoder.encode(data));
        });
    }

    group.finish();
}

/// Benchmark TSV encoding at various data sizes.
fn bench_tsv_encoding(c: &mut Criterion) {
    let mut group = c.benchmark_group("tsv_encode");

    for size in [100, 1000, 10000] {
        let data = generate_tabular(size);

        group.bench_with_input(BenchmarkId::new("tabular", size), &data, |b, data| {
            let encoder = TsvEncoder::new();
            b.iter(|| encoder.encode(data));
        });
    }

    // API response (uniform objects)
    for size in [100, 1000, 10000] {
        let data = generate_api_response(size);

        group.bench_with_input(BenchmarkId::new("api_response", size), &data, |b, data| {
            let encoder = TsvEncoder::new();
            b.iter(|| encoder.encode(data));
        });
    }

    group.finish();
}

/// Benchmark CSV encoding at various data sizes.
fn bench_csv_encoding(c: &mut Criterion) {
    let mut group = c.benchmark_group("csv_encode");

    for size in [100, 1000, 10000] {
        let data = generate_tabular(size);

        group.bench_with_input(BenchmarkId::new("tabular", size), &data, |b, data| {
            let encoder = CsvEncoder::new();
            b.iter(|| encoder.encode(data));
        });
    }

    group.finish();
}

/// Compare all encoders on the same data.
fn bench_encoder_comparison(c: &mut Criterion) {
    let mut group = c.benchmark_group("encoder_comparison");

    // Use medium-sized API response for comparison
    let data = generate_api_response(1000);

    group.bench_with_input(BenchmarkId::new("toon", "1k_objects"), &data, |b, data| {
        let encoder = ToonEncoder::new();
        b.iter(|| encoder.encode(data));
    });

    group.bench_with_input(BenchmarkId::new("json", "1k_objects"), &data, |b, data| {
        let encoder = JsonEncoder::new(false);
        b.iter(|| encoder.encode(data));
    });

    group.bench_with_input(BenchmarkId::new("yaml", "1k_objects"), &data, |b, data| {
        let encoder = YamlEncoder::new();
        b.iter(|| encoder.encode(data));
    });

    group.bench_with_input(BenchmarkId::new("tsv", "1k_objects"), &data, |b, data| {
        let encoder = TsvEncoder::new();
        b.iter(|| encoder.encode(data));
    });

    group.bench_with_input(BenchmarkId::new("csv", "1k_objects"), &data, |b, data| {
        let encoder = CsvEncoder::new();
        b.iter(|| encoder.encode(data));
    });

    group.finish();
}

/// Compare encoder outputs for token savings analysis.
fn bench_mixed_types(c: &mut Criterion) {
    let mut group = c.benchmark_group("mixed_types");

    for size in [100, 1000] {
        let data = generate_mixed_types(size);

        group.bench_with_input(BenchmarkId::new("toon", size), &data, |b, data| {
            let encoder = ToonEncoder::new();
            b.iter(|| encoder.encode(data));
        });

        group.bench_with_input(BenchmarkId::new("json", size), &data, |b, data| {
            let encoder = JsonEncoder::new(false);
            b.iter(|| encoder.encode(data));
        });
    }

    group.finish();
}

/// Rough estimate of Value size in bytes for throughput calculation.
fn estimate_value_size(value: &Value) -> usize {
    match value {
        Value::Null => 4,
        Value::Bool(_) => 5,
        Value::Number(_) => 8,
        Value::String(s) => s.len() + 2,
        Value::Array(arr) => arr.iter().map(estimate_value_size).sum::<usize>() + 2,
        Value::Object(obj) => {
            obj.iter()
                .map(|(k, v)| k.len() + 3 + estimate_value_size(v))
                .sum::<usize>()
                + 2
        }
    }
}

criterion_group!(
    benches,
    bench_toon_encoding,
    bench_json_encoding,
    bench_yaml_encoding,
    bench_tsv_encoding,
    bench_csv_encoding,
    bench_encoder_comparison,
    bench_mixed_types,
);

criterion_main!(benches);
