"""CLI entry point for llm-fmt."""

import json
import sys
import traceback
from pathlib import Path

import click

from llm_fmt import __version__
from llm_fmt.analyze import analyze, format_report, report_to_dict, select_format
from llm_fmt.config import load_config
from llm_fmt.errors import ConfigError, InputError, LLMFmtError, OutputError
from llm_fmt.filters import IncludeFilter, MaxDepthFilter
from llm_fmt.parsers import CsvParser, JsonParser, XmlParser, YamlParser
from llm_fmt.pipeline import PipelineBuilder
from llm_fmt.tokens import TOKENIZERS, count_tokens_safe, estimate_tokens

PARSER_MAP: dict[str, type[JsonParser | YamlParser | XmlParser | CsvParser]] = {
    "json": JsonParser,
    "yaml": YamlParser,
    "xml": XmlParser,
    "csv": CsvParser,
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
    type=click.Choice(["toon", "json", "yaml", "tsv", "csv", "auto"]),
    default=None,
    help="Output format (default: auto or from config).",
)
@click.option(
    "--input-format",
    "-F",
    "input_format",
    type=click.Choice(["json", "yaml", "xml", "csv", "auto"]),
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
@click.pass_context
def main(  # noqa: PLR0913
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
    debug: bool,  # noqa: FBT001
    input_file: Path | None,
) -> None:
    """Convert JSON/YAML/XML to token-efficient formats for LLM contexts.

    Supports TOON, compact JSON, YAML, and TSV output formats.
    Reduces token consumption by 30-60% when passing structured data to LLMs.

    Filters use JMESPath syntax (e.g., users[*].email, items[?active]).
    """
    # Store debug flag in context for error handling
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug

    try:
        _run_main(
            ctx=ctx,
            config_path=config_path,
            output_format=output_format,
            input_format=input_format,
            include_patterns=include_patterns,
            max_depth=max_depth,
            output_file=output_file,
            sort_keys=sort_keys,
            no_color=no_color,
            count_tokens=count_tokens,
            tokenizer=tokenizer,
            analyze=analyze,
            output_json=output_json,
            input_file=input_file,
        )
    except LLMFmtError as e:
        _handle_error(ctx, e)
    except Exception as e:
        # Catch unexpected errors
        if debug:
            raise
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)


def _handle_error(ctx: click.Context, error: LLMFmtError) -> None:
    """Handle LLMFmtError exceptions with proper exit codes.

    Args:
        ctx: Click context.
        error: The error to handle.
    """
    debug = ctx.obj.get("debug", False) if ctx.obj else False

    if debug:
        # Show full traceback in debug mode
        click.echo(traceback.format_exc(), err=True)
    else:
        # Show clean error message
        click.echo(f"Error: {error}", err=True)

    ctx.exit(error.exit_code)


def _run_main(  # noqa: PLR0912, PLR0913, PLR0915
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
    """Main CLI logic.

    Args:
        ctx: Click context.
        config_path: Path to config file.
        output_format: Output format (toon, json, yaml, tsv, auto).
        input_format: Input format (json, yaml, auto).
        include_patterns: JMESPath filter patterns.
        max_depth: Maximum depth to traverse.
        output_file: Output file path.
        sort_keys: Sort object keys alphabetically.
        no_color: Disable colored output.
        count_tokens: Show token count.
        tokenizer: Tokenizer name.
        analyze: Run analysis mode.
        output_json: Output analysis as JSON.
        input_file: Input file path.
    """
    # Load configuration
    config = load_config(config_path)

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
            raise InputError(msg)
        try:
            data = input_file.read_bytes()
        except OSError as e:
            msg = f"Cannot read file: {input_file}: {e}"
            raise InputError(msg) from e
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
        parsed_data = parser.parse(data)
        actual_format = select_format(parsed_data)
        click.echo(f"Auto-selected format: {actual_format}", err=True)

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
            raise ConfigError(msg) from e

    if effective_max_depth is not None:
        try:
            builder.add_filter(MaxDepthFilter(effective_max_depth))
        except ValueError as e:
            msg = f"--max-depth: {e}"
            raise ConfigError(msg) from e

    # Run pipeline
    pipeline = builder.build()
    result = pipeline.run(data)

    # Output to file or stdout
    if output_file:
        try:
            output_file.write_text(result, encoding="utf-8")
        except OSError as e:
            msg = f"Cannot write file: {output_file}: {e}"
            raise OutputError(msg) from e
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
    parsed_data = parser.parse(data)

    # Run analysis
    report = analyze(parsed_data, tokenizer)

    # Output report
    if output_json:
        click.echo(json.dumps(report_to_dict(report), indent=2))
    else:
        click.echo(format_report(report, use_color=not no_color))


def _detect_parser(
    filename: Path | None, data: bytes
) -> JsonParser | YamlParser | XmlParser | CsvParser:
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
        if suffix == ".xml":
            return XmlParser()
        if suffix == ".csv":
            return CsvParser()
        if suffix == ".tsv":
            return CsvParser(delimiter="\t")

    # Try to detect from content
    text = data.decode("utf-8", errors="replace").strip()
    if text.startswith(("{", "[")):
        return JsonParser()
    if text.startswith(("<?xml", "<")):
        return XmlParser()

    # Default to YAML (it can parse most JSON too)
    return YamlParser()


if __name__ == "__main__":
    main()
