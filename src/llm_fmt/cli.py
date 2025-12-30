"""CLI entry point for llm-fmt."""

import json
import sys
from pathlib import Path

import click

from llm_fmt import __version__
from llm_fmt.analyze import analyze, format_report, report_to_dict, select_format
from llm_fmt.config import load_config
from llm_fmt.errors import ConfigError, EncodeError, ParseError
from llm_fmt.filters import IncludeFilter, MaxDepthFilter
from llm_fmt.parsers import JsonParser, YamlParser
from llm_fmt.pipeline import PipelineBuilder
from llm_fmt.tokens import TOKENIZERS, count_tokens_safe, estimate_tokens

PARSER_MAP: dict[str, type[JsonParser | YamlParser]] = {
    "json": JsonParser,
    "yaml": YamlParser,
}


@click.command()
@click.version_option(version=__version__, prog_name="llm-fmt")
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to config file (default: .llm-fmt.toml in current or home dir).",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["toon", "json", "yaml", "auto"]),
    default=None,
    help="Output format (default: auto or from config).",
)
@click.option(
    "--input-format",
    "-F",
    "input_format",
    type=click.Choice(["json", "yaml", "auto"]),
    default="auto",
    help="Input format (default: auto-detect).",
)
@click.option(
    "--filter",
    "-i",
    "include_patterns",
    multiple=True,
    help="JMESPath expression to extract data. Can be repeated.",
)
@click.option(
    "--max-depth",
    "-d",
    "max_depth",
    type=int,
    default=None,
    help="Maximum depth to traverse (applied after filters).",
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
    "--no-color",
    is_flag=True,
    help="Disable colored output.",
)
@click.option(
    "--count-tokens",
    is_flag=True,
    help="Show token count for output.",
)
@click.option(
    "--tokenizer",
    type=click.Choice(list(TOKENIZERS.keys())),
    default=None,
    help="Tokenizer for counting (default: cl100k_base or from config).",
)
@click.option(
    "--analyze",
    is_flag=True,
    help="Compare token counts across formats and recommend optimal choice.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output analysis in JSON format (only with --analyze).",
)
@click.argument(
    "input_file",
    type=click.Path(path_type=Path),
    required=False,
)
@click.pass_context
def main(  # noqa: PLR0912, PLR0913, PLR0915
    ctx: click.Context,
    config_path: Path | None,
    output_format: str | None,
    input_format: str,
    include_patterns: tuple[str, ...],
    max_depth: int | None,
    output_file: Path | None,
    sort_keys: bool,  # noqa: FBT001
    no_color: bool,  # noqa: FBT001
    count_tokens: bool,  # noqa: FBT001
    tokenizer: str | None,
    analyze: bool,  # noqa: FBT001
    output_json: bool,  # noqa: FBT001
    input_file: Path | None,
) -> None:
    """Convert JSON/YAML/XML to token-efficient formats for LLM contexts.

    Supports TOON, compact JSON, and YAML output formats.
    Reduces token consumption by 30-60% when passing structured data to LLMs.

    Filters use JMESPath syntax (e.g., users[*].email, items[?active]).
    """
    # Load configuration
    try:
        config = load_config(config_path)
    except ConfigError as e:
        msg = str(e)
        raise click.ClickException(msg) from e

    # Apply config defaults for unset CLI options
    effective_format = output_format if output_format is not None else config.format
    effective_tokenizer = tokenizer if tokenizer is not None else config.tokenizer
    # CLI --no-color overrides config; otherwise use config setting
    effective_no_color = no_color or not config.output.color
    effective_max_depth = max_depth if max_depth is not None else config.filter.default_max_depth

    # Read input
    if input_file is None:
        # Check if stdin is a TTY (interactive terminal with no piped input)
        if sys.stdin.isatty():
            click.echo(ctx.get_help())
            ctx.exit(0)
        data = sys.stdin.buffer.read()
        filename: Path | None = None
    else:
        if not input_file.exists():
            msg = f"File not found: {input_file}"
            raise click.ClickException(msg)
        data = input_file.read_bytes()
        filename = input_file

    # Analysis mode
    if analyze:
        _run_analysis(
            data, input_format, filename, effective_tokenizer, output_json, effective_no_color
        )
        return

    # Determine parser
    parser = _detect_parser(filename, data) if input_format == "auto" else PARSER_MAP[input_format]()

    # Handle auto format selection
    actual_format = effective_format
    if effective_format == "auto":
        try:
            parsed_data = parser.parse(data)
            actual_format = select_format(parsed_data)
            click.echo(f"Auto-selected format: {actual_format}", err=True)
        except ParseError as e:
            msg = f"Parse error: {e}"
            raise click.ClickException(msg) from e

    # Build pipeline
    builder = PipelineBuilder()
    builder.with_parser(parser)

    # Configure encoder
    builder.with_format(actual_format, sort_keys=sort_keys)

    # Add filters: all --filter expressions first, then --max-depth last
    for i, pattern in enumerate(include_patterns):
        try:
            builder.add_filter(IncludeFilter(pattern))
        except ValueError as e:
            msg = f"--filter[{i}]: {e}"
            raise click.ClickException(msg) from e

    if effective_max_depth is not None:
        try:
            builder.add_filter(MaxDepthFilter(effective_max_depth))
        except ValueError as e:
            msg = f"--max-depth: {e}"
            raise click.ClickException(msg) from e

    # Run pipeline
    try:
        pipeline = builder.build()
        result = pipeline.run(data)

        # Output to file or stdout
        if output_file:
            output_file.write_text(result, encoding="utf-8")
            click.echo(f"Written to {output_file}", err=True)
        else:
            click.echo(result, nl=False)

        # Token counting
        if count_tokens:
            token_count = count_tokens_safe(result, effective_tokenizer)
            if token_count is not None:
                click.echo(f"Tokens ({effective_tokenizer}): {token_count}", err=True)
            else:
                estimated = estimate_tokens(result)
                click.echo(f"Tokens (estimated): ~{estimated}", err=True)
    except ParseError as e:
        msg = f"Parse error: {e}"
        raise click.ClickException(msg) from e
    except EncodeError as e:
        msg = f"Encode error: {e}"
        raise click.ClickException(msg) from e


def _run_analysis(
    data: bytes,
    input_format: str,
    filename: Path | None,
    tokenizer: str,
    output_json: bool,  # noqa: FBT001
    no_color: bool,  # noqa: FBT001
) -> None:
    """Run analysis mode and output report.

    Args:
        data: Raw input data.
        input_format: Input format (json, yaml, auto).
        filename: Input filename for auto-detection.
        tokenizer: Tokenizer name.
        output_json: Output as JSON.
        no_color: Disable colors.
    """
    # Parse input to get Python object
    parser = _detect_parser(filename, data) if input_format == "auto" else PARSER_MAP[input_format]()

    try:
        parsed_data = parser.parse(data)
    except ParseError as e:
        msg = f"Parse error: {e}"
        raise click.ClickException(msg) from e

    # Run analysis
    report = analyze(parsed_data, tokenizer)

    # Output report
    if output_json:
        click.echo(json.dumps(report_to_dict(report), indent=2))
    else:
        click.echo(format_report(report, use_color=not no_color))


def _detect_parser(filename: Path | None, data: bytes) -> JsonParser | YamlParser:
    """Detect parser based on filename or content.

    Args:
        filename: Input filename.
        data: Raw data.

    Returns:
        Parser instance.
    """
    # Try filename extension first
    if filename:
        suffix = filename.suffix.lower()
        if suffix in {".json", ".jsonl"}:
            return JsonParser()
        if suffix in {".yaml", ".yml"}:
            return YamlParser()

    # Try to detect from content
    text = data.decode("utf-8", errors="replace").strip()
    if text.startswith(("{", "[")):
        return JsonParser()

    # Default to YAML (it can parse most JSON too)
    return YamlParser()


if __name__ == "__main__":
    main()
