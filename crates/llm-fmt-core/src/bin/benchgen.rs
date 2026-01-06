//! Benchmark data generator.
//!
//! Generates synthetic benchmark data files in various formats.
//!
//! Usage:
//!   cargo run --bin benchgen -- [output_dir]
//!
//! If output_dir is not specified, defaults to "data/benchmark".

use std::env;
use std::fs;
use std::path::Path;

use llm_fmt_core::benchdata::{
    generate_api_response, generate_mixed_types, generate_nested_config, generate_sparse_array,
    generate_tabular, value_to_csv, value_to_json, value_to_xml, value_to_yaml,
};

fn main() {
    let args: Vec<String> = env::args().collect();
    let output_dir = args.get(1).map_or("data/benchmark", String::as_str);

    println!("Generating benchmark data to: {output_dir}");

    // Create directories
    let json_dir = Path::new(output_dir).join("json");
    let yaml_dir = Path::new(output_dir).join("yaml");
    let xml_dir = Path::new(output_dir).join("xml");
    let csv_dir = Path::new(output_dir).join("csv");

    fs::create_dir_all(&json_dir).expect("Failed to create json directory");
    fs::create_dir_all(&yaml_dir).expect("Failed to create yaml directory");
    fs::create_dir_all(&xml_dir).expect("Failed to create xml directory");
    fs::create_dir_all(&csv_dir).expect("Failed to create csv directory");

    // Generate JSON files
    println!("Generating JSON files...");

    // API response - uniform objects (best case for TOON)
    for (name, count) in [("small", 100), ("medium", 1000), ("large", 10000)] {
        let data = generate_api_response(count);
        let json = value_to_json(&data);
        let path = json_dir.join(format!("api_response_{name}.json"));
        fs::write(&path, &json).expect("Failed to write JSON file");
        println!("  {} ({} bytes)", path.display(), json.len());
    }

    // Nested config - deep structure
    for (name, depth) in [("shallow", 5), ("medium", 10), ("deep", 20)] {
        let data = generate_nested_config(depth);
        let json = value_to_json(&data);
        let path = json_dir.join(format!("nested_config_{name}.json"));
        fs::write(&path, &json).expect("Failed to write JSON file");
        println!("  {} ({} bytes)", path.display(), json.len());
    }

    // Mixed types - heterogeneous data
    for (name, count) in [("small", 100), ("medium", 1000), ("large", 10000)] {
        let data = generate_mixed_types(count);
        let json = value_to_json(&data);
        let path = json_dir.join(format!("mixed_types_{name}.json"));
        fs::write(&path, &json).expect("Failed to write JSON file");
        println!("  {} ({} bytes)", path.display(), json.len());
    }

    // Sparse array - non-uniform objects
    for (name, count) in [("small", 100), ("medium", 1000), ("large", 10000)] {
        let data = generate_sparse_array(count);
        let json = value_to_json(&data);
        let path = json_dir.join(format!("sparse_array_{name}.json"));
        fs::write(&path, &json).expect("Failed to write JSON file");
        println!("  {} ({} bytes)", path.display(), json.len());
    }

    // Generate YAML files (same data shapes)
    println!("Generating YAML files...");

    for (name, count) in [("small", 100), ("medium", 1000), ("large", 10000)] {
        let data = generate_api_response(count);
        let yaml = value_to_yaml(&data);
        let path = yaml_dir.join(format!("api_response_{name}.yaml"));
        fs::write(&path, &yaml).expect("Failed to write YAML file");
        println!("  {} ({} bytes)", path.display(), yaml.len());
    }

    for (name, depth) in [("shallow", 5), ("medium", 10), ("deep", 20)] {
        let data = generate_nested_config(depth);
        let yaml = value_to_yaml(&data);
        let path = yaml_dir.join(format!("nested_config_{name}.yaml"));
        fs::write(&path, &yaml).expect("Failed to write YAML file");
        println!("  {} ({} bytes)", path.display(), yaml.len());
    }

    // Generate XML files
    println!("Generating XML files...");

    for (name, count) in [("small", 100), ("medium", 1000), ("large", 10000)] {
        let data = generate_api_response(count);
        let xml = value_to_xml(&data, "users");
        let path = xml_dir.join(format!("api_response_{name}.xml"));
        fs::write(&path, &xml).expect("Failed to write XML file");
        println!("  {} ({} bytes)", path.display(), xml.len());
    }

    for (name, depth) in [("shallow", 5), ("medium", 10), ("deep", 20)] {
        let data = generate_nested_config(depth);
        let xml = value_to_xml(&data, "config");
        let path = xml_dir.join(format!("nested_config_{name}.xml"));
        fs::write(&path, &xml).expect("Failed to write XML file");
        println!("  {} ({} bytes)", path.display(), xml.len());
    }

    // Generate CSV files (tabular data only - makes sense for CSV)
    println!("Generating CSV files...");

    for (name, count) in [("small", 100), ("medium", 1000), ("large", 10000)] {
        let data = generate_tabular(count);
        if let Some(csv_content) = value_to_csv(&data) {
            let path = csv_dir.join(format!("tabular_{name}.csv"));
            fs::write(&path, &csv_content).expect("Failed to write CSV file");
            println!("  {} ({} bytes)", path.display(), csv_content.len());
        }
    }

    // Also generate API response as CSV (flat enough to work)
    for (name, count) in [("small", 100), ("medium", 1000), ("large", 10000)] {
        let data = generate_api_response(count);
        if let Some(csv_content) = value_to_csv(&data) {
            let path = csv_dir.join(format!("api_response_{name}.csv"));
            fs::write(&path, &csv_content).expect("Failed to write CSV file");
            println!("  {} ({} bytes)", path.display(), csv_content.len());
        }
    }

    println!("\nDone! Generated benchmark data files.");
}
