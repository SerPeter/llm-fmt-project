"""Analysis mode for comparing token efficiency across formats."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from llm_fmt.encoders import JsonEncoder, ToonEncoder, YamlEncoder
from llm_fmt.errors import EncodeError
from llm_fmt.tokens import count_tokens, estimate_tokens
from llm_fmt.tokens import is_available as tiktoken_available


@dataclass
class DataShape:
    """Describes the shape and structure of data."""

    is_array: bool = False
    is_uniform_array: bool = False
    array_length: int = 0
    field_count: int = 0
    max_depth: int = 0
    is_mostly_primitives: bool = True
    description: str = ""
    sample_keys: list[str] = field(default_factory=list)


@dataclass
class FormatAnalysis:
    """Token analysis for a single output format."""

    name: str
    tokens: int
    savings_percent: float
    recommended: bool = False
    output: str = field(default="", repr=False)


@dataclass
class AnalysisReport:
    """Complete analysis report comparing formats."""

    original_tokens: int
    formats: list[FormatAnalysis]
    data_shape: DataShape
    recommendation: str
    recommendation_reason: str
    tokenizer: str = "cl100k_base"
    is_estimated: bool = False


def detect_data_shape(data: Any, max_sample: int = 100) -> DataShape:  # noqa: ANN401
    """Detect the shape and structure of data.

    Args:
        data: Input data to analyze.
        max_sample: Maximum items to sample from arrays for efficiency.

    Returns:
        DataShape describing the data structure.
    """
    shape = DataShape()

    if isinstance(data, list):
        shape.is_array = True
        shape.array_length = len(data)

        # Sample large arrays for efficiency
        sample = data[:max_sample] if len(data) > max_sample else data

        if sample and all(isinstance(item, dict) for item in sample):
            # Check if uniform (all objects have same keys)
            first_keys = set(sample[0].keys())
            shape.is_uniform_array = all(set(item.keys()) == first_keys for item in sample)
            shape.field_count = len(first_keys)
            shape.sample_keys = sorted(first_keys)[:10]  # Store up to 10 sample keys

        shape.description = _describe_array(data, shape)
        shape.max_depth = _calculate_depth_sampled(sample)
        shape.is_mostly_primitives = _check_mostly_primitives_sampled(sample)

    elif isinstance(data, dict):
        shape.field_count = len(data)
        shape.sample_keys = sorted(data.keys())[:10]
        shape.description = _describe_object(data)
        shape.max_depth = _calculate_depth(data)
        shape.is_mostly_primitives = _check_mostly_primitives(data)

    else:
        shape.description = f"Primitive value ({type(data).__name__})"
        shape.max_depth = 0
        shape.is_mostly_primitives = True

    return shape


def _describe_array(data: list[Any], shape: DataShape) -> str:
    """Generate description for array data."""
    if not data:
        return "Empty array"

    if shape.is_uniform_array:
        return f"Uniform array of {shape.array_length} objects with {shape.field_count} fields"

    if all(isinstance(item, dict) for item in data):
        return f"Array of {shape.array_length} objects with varying schemas"

    if all(not isinstance(item, (dict, list)) for item in data):
        return f"Array of {shape.array_length} primitives"

    return f"Mixed array of {shape.array_length} items"


def _describe_object(data: dict[str, Any]) -> str:
    """Generate description for object data."""
    if not data:
        return "Empty object"

    nested_count = sum(1 for v in data.values() if isinstance(v, (dict, list)))
    if nested_count == 0:
        return f"Flat object with {len(data)} fields"

    return f"Nested object with {len(data)} top-level fields"


def _calculate_depth(data: Any, current: int = 0) -> int:  # noqa: ANN401
    """Calculate maximum nesting depth."""
    if isinstance(data, dict):
        if not data:
            return current
        return max(_calculate_depth(v, current + 1) for v in data.values())

    if isinstance(data, list):
        if not data:
            return current
        return max(_calculate_depth(item, current + 1) for item in data)

    return current


def _calculate_depth_sampled(sample: list[Any]) -> int:
    """Calculate maximum nesting depth for sampled array items.

    Args:
        sample: Sampled list items to analyze.

    Returns:
        Maximum depth found in sample (adds 1 for array level).
    """
    if not sample:
        return 1  # Empty array has depth 1

    max_item_depth = max(_calculate_depth(item) for item in sample)
    return max_item_depth + 1  # Add 1 for the array level itself


def _check_mostly_primitives_sampled(sample: list[Any], threshold: float = 0.7) -> bool:
    """Check if sampled array items are mostly primitive values.

    Args:
        sample: Sampled list items to analyze.
        threshold: Ratio threshold for primitive vs complex.

    Returns:
        True if primitives dominate the sample.
    """
    if not sample:
        return True

    # Check if it's an array of primitives
    if all(not isinstance(item, (dict, list)) for item in sample):
        return True

    # For array of objects, check the objects
    primitive_count = 0
    complex_count = 0

    for item in sample:
        if isinstance(item, dict):
            for value in item.values():
                if isinstance(value, (dict, list)):
                    complex_count += 1
                else:
                    primitive_count += 1
        elif isinstance(item, list):
            complex_count += 1
        else:
            primitive_count += 1

    total = primitive_count + complex_count
    return total == 0 or (primitive_count / total) >= threshold


def _check_mostly_primitives(data: Any, threshold: float = 0.7) -> bool:  # noqa: ANN401
    """Check if data is mostly primitive values."""
    primitive_count = 0
    complex_count = 0

    def count_values(obj: Any) -> None:  # noqa: ANN401
        nonlocal primitive_count, complex_count

        if isinstance(obj, dict):
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    complex_count += 1
                    count_values(value)
                else:
                    primitive_count += 1
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    complex_count += 1
                    count_values(item)
                else:
                    primitive_count += 1
        else:
            primitive_count += 1

    count_values(data)
    total = primitive_count + complex_count
    return total == 0 or (primitive_count / total) >= threshold


def analyze(data: Any, tokenizer: str = "cl100k_base") -> AnalysisReport:  # noqa: ANN401
    """Analyze data and compare format efficiency.

    Args:
        data: Input data to analyze.
        tokenizer: Tokenizer name for token counting.

    Returns:
        AnalysisReport with token counts and recommendation.
    """
    # Check tiktoken availability
    use_estimation = not tiktoken_available()

    # Generate baseline (pretty JSON)
    pretty_json = json.dumps(data, indent=2, ensure_ascii=False)

    # Helper function to count tokens based on availability
    def count_fn(text: str) -> int:
        return estimate_tokens(text) if use_estimation else count_tokens(text, tokenizer)

    # Count baseline tokens
    baseline_tokens = count_fn(pretty_json)

    # Generate all format outputs and count tokens
    formats_data: list[tuple[str, str | None, str | None]] = [
        ("JSON (pretty)", pretty_json, None),
        ("Compact JSON", None, "compact_json"),
        ("YAML", None, "yaml"),
        ("TOON", None, "toon"),
    ]

    formats: list[FormatAnalysis] = []

    for name, precomputed_output, encoder_type in formats_data:
        if precomputed_output is None:
            # Generate output
            encoded_output = _encode_format(data, encoder_type)  # type: ignore[arg-type]
            if encoded_output is None:
                continue  # Skip if encoding failed
            output_text = encoded_output
        else:
            output_text = precomputed_output

        tokens = count_fn(output_text)

        savings = ((baseline_tokens - tokens) / baseline_tokens * 100) if baseline_tokens > 0 else 0.0

        formats.append(
            FormatAnalysis(
                name=name,
                tokens=tokens,
                savings_percent=round(savings, 1),
                output=output_text,
            )
        )

    # Detect data shape
    shape = detect_data_shape(data)

    # Determine recommendation
    recommendation, reason = _recommend_format(shape, formats)

    # Mark recommended format
    for fmt in formats:
        fmt.recommended = fmt.name == recommendation

    # Sort by token count
    formats.sort(key=lambda f: f.tokens)

    return AnalysisReport(
        original_tokens=baseline_tokens,
        formats=formats,
        data_shape=shape,
        recommendation=recommendation,
        recommendation_reason=reason,
        tokenizer=tokenizer,
        is_estimated=use_estimation,
    )


def _encode_format(data: Any, format_type: str) -> str | None:  # noqa: ANN401
    """Encode data to a specific format.

    Args:
        data: Data to encode.
        format_type: Type of format (compact_json, yaml, toon).

    Returns:
        Encoded string or None if encoding failed.
    """
    try:
        if format_type == "compact_json":
            return JsonEncoder().encode(data)
        if format_type == "yaml":
            return YamlEncoder().encode(data)
        if format_type == "toon":
            return ToonEncoder().encode(data)
    except EncodeError:
        return None
    return None


def _recommend_format(shape: DataShape, formats: list[FormatAnalysis]) -> tuple[str, str]:
    """Determine best format based on data shape.

    Args:
        shape: Data shape information.
        formats: List of format analyses.

    Returns:
        Tuple of (format_name, reason).
    """
    # TOON is best for uniform arrays
    if shape.is_uniform_array and shape.array_length > 1:
        toon_fmt = next((f for f in formats if f.name == "TOON"), None)
        if toon_fmt:
            return (
                "TOON",
                f"Uniform array of {shape.array_length} objects with {shape.field_count} fields",
            )

    # YAML is good for shallow, mostly primitive structures
    if shape.max_depth <= 2 and shape.is_mostly_primitives:  # noqa: PLR2004
        yaml_fmt = next((f for f in formats if f.name == "YAML"), None)
        if yaml_fmt:
            return "YAML", "Shallow structure with mostly primitive values"

    # Default: pick lowest token count that's not the baseline
    non_baseline = [f for f in formats if f.name != "JSON (pretty)"]
    if non_baseline:
        best = min(non_baseline, key=lambda f: f.tokens)
        return best.name, f"Lowest token count ({best.tokens:,} tokens)"

    return "Compact JSON", "Default efficient format"


def format_report(report: AnalysisReport, *, use_color: bool = True) -> str:  # noqa: ARG001
    """Format analysis report for terminal output.

    Args:
        report: Analysis report to format.
        use_color: Whether to use ANSI color codes.

    Returns:
        Formatted string for terminal display.
    """
    lines: list[str] = []

    # Header
    estimation_note = " (estimated)" if report.is_estimated else ""
    lines.append(f"Token Analysis ({report.tokenizer} tokenizer){estimation_note}")
    lines.append("")

    # Table header
    lines.append(f"{'Format':<18} {'Tokens':>10} {'Savings':>10}   ")
    lines.append("-" * 50)

    # Format rows
    for fmt in report.formats:
        name = fmt.name
        tokens = f"{fmt.tokens:,}"
        savings = f"{fmt.savings_percent:+.0f}%" if fmt.savings_percent != 0 else "baseline"

        marker = ""
        if fmt.recommended:
            marker = " <- recommended"
        elif fmt.name == "JSON (pretty)":
            marker = " (baseline)"

        lines.append(f"{name:<18} {tokens:>10} {savings:>10}   {marker}")

    lines.append("")

    # Data shape
    lines.append(f"Data shape: {report.data_shape.description}")

    # Recommendation
    best = next((f for f in report.formats if f.recommended), None)
    if best and best.name != "JSON (pretty)":
        tokens_saved = report.original_tokens - best.tokens
        lines.append(
            f"Recommendation: {best.name} saves {tokens_saved:,} tokens "
            f"({best.savings_percent:.0f}%) per request"
        )

        # Usage hint
        fmt_arg = best.name.lower().replace(" ", "-")
        if fmt_arg == "compact-json":
            fmt_arg = "json"
        lines.append("")
        lines.append(f"Use: llm-fmt <input> --format {fmt_arg}")

    return "\n".join(lines)


def report_to_dict(report: AnalysisReport) -> dict[str, Any]:
    """Convert analysis report to dictionary for JSON output.

    Args:
        report: Analysis report to convert.

    Returns:
        Dictionary representation.
    """
    return {
        "original_tokens": report.original_tokens,
        "tokenizer": report.tokenizer,
        "is_estimated": report.is_estimated,
        "formats": [
            {
                "name": fmt.name,
                "tokens": fmt.tokens,
                "savings_percent": fmt.savings_percent,
                "recommended": fmt.recommended,
            }
            for fmt in report.formats
        ],
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
    }
