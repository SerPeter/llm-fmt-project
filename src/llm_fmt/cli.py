"""CLI entry point for llm-fmt."""

import json
import sys
from pathlib import Path

import click

from llm_fmt import __version__
from llm_fmt.config import Config, load_config

# Import the Rust native module
try:
    from llm_fmt._native import (
        analyze as rust_analyze,
        convert as rust_convert,
        is_available,
        version as rust_version,
    )

    RUST_AVAILABLE = is_available()
except ImportError:
    RUST_AVAILABLE = False
    rust_convert = None
    rust_analyze = None
    rust_version = lambda: "N/A"


class StrictModeError(Exception):
    """Raised when strict mode is enabled and limits are exceeded."""


@click.command()
@click.version_option(version=__version__, prog_name="llm-fmt")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    help="Explicit config file path (skip search).",
)
@click.option(
    "--no-config",
    is_flag=True,
    help="Ignore all config files, use defaults only.",
)
@click.option(
    "--show-config",
    is_flag=True,
    help="Print resolved configuration and exit.",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["auto", "toon", "json", "yaml", "tsv", "csv"]),
    default=None,
    help="Output format (from config or 'auto').",
)
@click.option(
    "--input-format",
    "-F",
    "input_format",
    type=click.Choice(["json", "yaml", "xml", "csv", "tsv", "auto"]),
    default=None,
    help="Input format (from config or 'auto').",
)
@click.option(
    "--filter",
    "-i",
    "include_pattern",
    default=None,
    help="Path expression to extract data (e.g., users[*].name).",
)
@click.option(
    "--max-depth",
    "-d",
    "max_depth",
    type=int,
    default=None,
    help="Maximum depth to traverse (from config).",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output file (default: stdout).",
)
@click.option(
    "--sort-keys",
    is_flag=True,
    help="Sort object keys alphabetically (JSON format only).",
)
@click.option(
    "--max-items",
    type=int,
    default=None,
    help="Maximum items per array (from config).",
)
@click.option(
    "--max-string-length",
    type=int,
    default=None,
    help="Maximum length for string values (from config).",
)
@click.option(
    "--max-tokens",
    type=int,
    default=None,
    help="Maximum output tokens (from config).",
)
@click.option(
    "--truncation-strategy",
    type=click.Choice(["head", "tail", "sample", "balanced"]),
    default=None,
    help="Strategy for selecting items when truncating arrays (from config).",
)
@click.option(
    "--preserve",
    multiple=True,
    help="JSON paths to preserve from truncation (can be specified multiple times).",
)
@click.option(
    "--strict",
    "strict_flag",
    is_flag=True,
    flag_value=True,
    default=None,
    help="Error instead of truncating (overrides config).",
)
@click.option(
    "--no-strict",
    "strict_flag",
    is_flag=True,
    flag_value=False,
    help="Allow truncation (overrides config).",
)
@click.option(
    "--analyze",
    is_flag=True,
    help="Analyze data and show token comparison across formats.",
)
@click.option(
    "--analyze-json",
    is_flag=True,
    help="Output analysis as JSON (implies --analyze).",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Show full traceback on errors.",
)
@click.argument(
    "input_file",
    type=click.Path(path_type=Path),
    required=False,
)
def main(
    config_path: Path | None,
    no_config: bool,
    show_config: bool,
    output_format: str | None,
    input_format: str | None,
    include_pattern: str | None,
    max_depth: int | None,
    output_file: Path | None,
    sort_keys: bool,
    max_items: int | None,
    max_string_length: int | None,
    max_tokens: int | None,
    truncation_strategy: str | None,
    preserve: tuple[str, ...],
    strict_flag: bool | None,
    analyze: bool,
    analyze_json: bool,
    debug: bool,
    input_file: Path | None,
) -> None:
    """Convert JSON/YAML/XML/CSV to token-efficient formats for LLM contexts.

    Supports TOON, compact JSON, YAML, TSV, and CSV output formats.
    Reduces token consumption by 30-60% when passing structured data to LLMs.

    \b
    Configuration hierarchy (highest to lowest priority):
        1. CLI arguments
        2. Environment variables (LLM_FMT_* prefix)
        3. .llm-fmt.yaml / .llm-fmt.toml
        4. pyproject.toml [tool.llm-fmt]
        5. Strong defaults

    \b
    Examples:
        llm-fmt data.json                        # Convert to TOON (default)
        llm-fmt -f yaml data.json                # Convert to YAML
        llm-fmt -f tsv data.json                 # Convert to TSV
        llm-fmt -i "users[*].name" data.json     # Extract user names
        llm-fmt --max-items 10 data.json         # Limit arrays to 10 items
        llm-fmt --analyze data.json              # Show token comparison
        llm-fmt --analyze-json data.json         # Analysis as JSON
        llm-fmt --show-config                    # Show resolved config
        cat data.json | llm-fmt                  # Read from stdin
    """
    try:
        # Load configuration with hierarchy
        config = load_config(
            config_path=config_path,
            no_config=no_config,
            cli_overrides=_build_cli_overrides(
                output_format=output_format,
                input_format=input_format,
                max_depth=max_depth,
                max_items=max_items,
                max_string_length=max_string_length,
                max_tokens=max_tokens,
                truncation_strategy=truncation_strategy,
                strict=strict_flag,
            ),
        )

        # Handle --show-config
        if show_config:
            _print_config(config)
            return

        if not RUST_AVAILABLE:
            click.echo("Error: Rust native module not available. Please reinstall llm-fmt.", err=True)
            sys.exit(1)

        # Handle analyze_json implying analyze
        if analyze_json:
            analyze = True

        # Read input
        if input_file is None:
            if sys.stdin.isatty():
                click.echo(click.get_current_context().get_help())
                sys.exit(0)
            data = sys.stdin.buffer.read()
        else:
            if not input_file.exists():
                click.echo(f"Error: File not found: {input_file}", err=True)
                sys.exit(1)
            data = input_file.read_bytes()

        # Resolve format from config
        resolved_format = output_format if output_format is not None else config.format
        resolved_input_format = input_format if input_format is not None else config.input_format

        # Handle analyze mode
        if analyze:
            result = rust_analyze(data, input_format=resolved_input_format, output_json=analyze_json)
            if analyze_json:
                click.echo(json.dumps(result, indent=2))
            else:
                click.echo(result)
            return

        # Call Rust convert function
        result = rust_convert(
            data,
            format=resolved_format,
            input_format=resolved_input_format,
            max_depth=max_depth if max_depth is not None else config.limits.max_depth,
            sort_keys=sort_keys,
            include=include_pattern,
            max_items=max_items if max_items is not None else config.limits.max_items,
            max_string_length=max_string_length if max_string_length is not None else config.limits.max_string_length,
            truncation_strategy=truncation_strategy if truncation_strategy is not None else config.truncation.strategy,
            preserve=list(preserve) if preserve else None,
        )

        # Check strict mode for token limits (basic check based on output size)
        if config.output.strict and config.limits.max_tokens:
            # Rough token estimation (4 chars per token average)
            estimated_tokens = len(result) // 4
            if estimated_tokens > config.limits.max_tokens:
                raise StrictModeError(
                    f"Output exceeds max_tokens limit (~{estimated_tokens:,} > {config.limits.max_tokens:,} tokens)\n"
                    f"Hint: Use --max-tokens to increase limit, or remove --strict to allow truncation"
                )

        # Output
        if output_file:
            output_file.write_text(result, encoding="utf-8")
            click.echo(f"Written to {output_file}", err=True)
        else:
            click.echo(result, nl=False)

    except StrictModeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        if debug:
            raise
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        if debug:
            raise
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _build_cli_overrides(
    output_format: str | None,
    input_format: str | None,
    max_depth: int | None,
    max_items: int | None,
    max_string_length: int | None,
    max_tokens: int | None,
    truncation_strategy: str | None,
    strict: bool | None,
) -> dict[str, object]:
    """Build CLI overrides dict with only non-None values."""
    overrides: dict[str, object] = {}

    if output_format is not None:
        overrides["format"] = output_format
    if input_format is not None:
        overrides["input_format"] = input_format
    if max_depth is not None:
        overrides["limits.max_depth"] = max_depth
    if max_items is not None:
        overrides["limits.max_items"] = max_items
    if max_string_length is not None:
        overrides["limits.max_string_length"] = max_string_length
    if max_tokens is not None:
        overrides["limits.max_tokens"] = max_tokens
    if truncation_strategy is not None:
        overrides["truncation.strategy"] = truncation_strategy
    if strict is not None:
        overrides["output.strict"] = strict

    return overrides


def _print_config(config: Config) -> None:
    """Print resolved configuration in YAML-like format."""
    click.echo("Resolved Configuration:")
    click.echo("=" * 40)

    d = config.to_dict()

    click.echo("\ndefaults:")
    click.echo(f"  format: {d['defaults']['format']}")
    click.echo(f"  input_format: {d['defaults']['input_format']}")

    click.echo("\nlimits:")
    click.echo(f"  max_tokens: {d['limits']['max_tokens']}")
    click.echo(f"  max_items: {d['limits']['max_items']}")
    click.echo(f"  max_string_length: {d['limits']['max_string_length']}")
    click.echo(f"  max_depth: {d['limits']['max_depth']}")

    click.echo("\ntruncation:")
    click.echo(f"  strategy: {d['truncation']['strategy']}")
    click.echo(f"  show_summary: {d['truncation']['show_summary']}")

    click.echo("\nfilter:")
    exclude = d["filter"]["default_exclude"]
    if exclude:
        click.echo(f"  default_exclude: {exclude}")
    else:
        click.echo("  default_exclude: []")

    click.echo("\noutput:")
    click.echo(f"  strict: {d['output']['strict']}")


if __name__ == "__main__":
    main()
