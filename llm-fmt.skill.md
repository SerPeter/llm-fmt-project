---
name: llm-fmt
description: Token-efficient data format converter for LLM contexts
allowed-tools: Bash
---

# llm-fmt

Token-efficient data format converter for LLM contexts. Reduces token consumption by 30-70% when passing structured data to LLMs.

## When to Use

Use llm-fmt when you need to:
- Convert JSON/YAML/XML/CSV data to a more token-efficient format before including in prompts
- Analyze data to find the optimal output format
- Truncate large datasets to fit context windows
- Filter data to include only relevant fields

## Installation

```bash
uvx llm-fmt --help
```

## Quick Reference

### Basic Conversion

```bash
# Convert to TOON (default, good for arrays of objects)
uvx llm-fmt data.json

# Convert to specific format
uvx llm-fmt data.json -f tsv      # Best for tabular data (60-75% savings)
uvx llm-fmt data.json -f toon     # Best for uniform arrays (45-60% savings)
uvx llm-fmt data.json -f yaml     # Best for nested configs (25-35% savings)
uvx llm-fmt data.json -f json     # Compact JSON (10-15% savings)

# Pipe from stdin
cat data.json | uvx llm-fmt -f toon
curl -s api.example.com/data | uvx llm-fmt -f tsv
```

### Filtering & Truncation

```bash
# Filter to specific paths
uvx llm-fmt data.json -i "users[*].name"
uvx llm-fmt data.json -i "results[0].data"

# Limit nesting depth
uvx llm-fmt data.json --max-depth 3

# Truncate large arrays
uvx llm-fmt data.json --max-items 50

# Truncate long strings
uvx llm-fmt data.json --max-string-length 200

# Truncation strategies
uvx llm-fmt data.json --max-items 10 --truncation-strategy head      # first N
uvx llm-fmt data.json --max-items 10 --truncation-strategy tail      # last N
uvx llm-fmt data.json --max-items 10 --truncation-strategy balanced  # start+end
uvx llm-fmt data.json --max-items 10 --truncation-strategy sample    # random

# Preserve specific paths from truncation
uvx llm-fmt data.json --max-items 5 --preserve "errors"
```

### Analysis

```bash
# Compare token usage across formats
uvx llm-fmt data.json --analyze

# Get analysis as JSON
uvx llm-fmt data.json --analyze-json
```

## Format Selection Guide

| Data Shape | Best Format | Savings |
|------------|-------------|---------|
| Uniform arrays (API responses, logs) | tsv or toon | 50-70% |
| Tabular/flat data | tsv | 70-75% |
| Mixed/sparse arrays | toon | 40-50% |
| Deeply nested configs | yaml | 30-35% |
| Complex mixed structures | json | 10-15% |

## Examples

### API Response Processing

```bash
# Fetch API data and convert to token-efficient format
curl -s https://api.github.com/repos/owner/repo/issues | uvx llm-fmt -f toon --max-items 20

# Extract specific fields
curl -s https://api.example.com/users | uvx llm-fmt -i "[*].{id,name,email}" -f tsv
```

### Large File Handling

```bash
# Truncate large JSON to fit context
uvx llm-fmt large-response.json --max-items 100 --max-string-length 500 -f toon

# Analyze before deciding
uvx llm-fmt large-response.json --analyze
```

## CLI Options

```
-f, --format          Output format: toon, json, yaml, tsv, csv (default: toon)
-F, --input-format    Input format: json, yaml, xml, csv, auto (default: auto)
-i, --filter          Path expression to extract data
-d, --max-depth       Maximum nesting depth
--max-items           Maximum items per array
--max-string-length   Maximum length for string values
--truncation-strategy Truncation strategy: head, tail, sample, balanced
--preserve            Paths to preserve from truncation (can repeat)
--analyze             Show token comparison across formats
--analyze-json        Output analysis as JSON
--strict              Error instead of truncating
--show-config         Print resolved configuration
-o, --output          Output file (default: stdout)
```
