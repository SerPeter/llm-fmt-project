"""CLI entry point for llm-fmt."""

import sys
from pathlib import Path

import click

from llm_fmt import __version__
from llm_fmt.errors import EncodeError, ParseError
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
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["toon", "json", "yaml"]),
    default="toon",
    help="Output format (default: toon).",
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
    default="cl100k_base",
    help="Tokenizer for counting (default: cl100k_base).",
)
@click.argument(
    "input_file",
    type=click.Path(path_type=Path),
    required=False,
)
@click.pass_context
def main(  # noqa: PLR0912, PLR0913, PLR0915
    ctx: click.Context,
    output_format: str,
    input_format: str,
    include_patterns: tuple[str, ...],
    max_depth: int | None,
    output_file: Path | None,
    sort_keys: bool,  # noqa: FBT001
    no_color: bool,  # noqa: ARG001, FBT001
    count_tokens: bool,  # noqa: FBT001
    tokenizer: str,
    input_file: Path | None,
) -> None:
    """Convert JSON/YAML/XML to token-efficient formats for LLM contexts.

    Supports TOON, compact JSON, and YAML output formats.
    Reduces token consumption by 30-60% when passing structured data to LLMs.

    Filters use JMESPath syntax (e.g., users[*].email, items[?active]).
    """
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

    # Build pipeline
    builder = PipelineBuilder()

    # Configure parser
    if input_format == "auto":
        builder.with_auto_parser(filename=filename, data=data)
    else:
        builder.with_parser(PARSER_MAP[input_format]())

    # Configure encoder
    builder.with_format(output_format, sort_keys=sort_keys)

    # Add filters: all --filter expressions first, then --max-depth last
    for i, pattern in enumerate(include_patterns):
        try:
            builder.add_filter(IncludeFilter(pattern))
        except ValueError as e:
            msg = f"--filter[{i}]: {e}"
            raise click.ClickException(msg) from e

    if max_depth is not None:
        try:
            builder.add_filter(MaxDepthFilter(max_depth))
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
            token_count = count_tokens_safe(result, tokenizer)
            if token_count is not None:
                click.echo(f"Tokens ({tokenizer}): {token_count}", err=True)
            else:
                estimated = estimate_tokens(result)
                click.echo(f"Tokens (estimated): ~{estimated}", err=True)
    except ParseError as e:
        msg = f"Parse error: {e}"
        raise click.ClickException(msg) from e
    except EncodeError as e:
        msg = f"Encode error: {e}"
        raise click.ClickException(msg) from e


if __name__ == "__main__":
    main()
