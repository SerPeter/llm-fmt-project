"""CLI entry point for llm-fmt."""

import sys
from pathlib import Path

import click

from llm_fmt import __version__
from llm_fmt.errors import ConfigurationError, EncodeError, ParseError
from llm_fmt.filters import ExcludeFilter, IncludeFilter, MaxDepthFilter
from llm_fmt.parsers import JsonParser, YamlParser
from llm_fmt.pipeline import PipelineBuilder


class OrderedCommand(click.Command):
    """Command that tracks order of filter options."""

    def make_context(
        self,
        info_name: str | None,
        args: list[str],
        parent: click.Context | None = None,
        **extra: object,
    ) -> click.Context:
        """Create context and track filter order."""
        ctx = super().make_context(info_name, args, parent, **extra)

        # Track order of filter-related arguments
        filter_order: list[tuple[str, str]] = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("--filter", "-i"):
                if i + 1 < len(args):
                    filter_order.append(("include", args[i + 1]))
                    i += 2
                    continue
            elif arg in ("--exclude", "-e"):
                if i + 1 < len(args):
                    filter_order.append(("exclude", args[i + 1]))
                    i += 2
                    continue
            elif arg in ("--max-depth", "-d"):
                if i + 1 < len(args):
                    filter_order.append(("depth", args[i + 1]))
                    i += 2
                    continue
            elif arg.startswith("--filter="):
                filter_order.append(("include", arg.split("=", 1)[1]))
            elif arg.startswith("--exclude="):
                filter_order.append(("exclude", arg.split("=", 1)[1]))
            elif arg.startswith("--max-depth="):
                filter_order.append(("depth", arg.split("=", 1)[1]))
            i += 1

        ctx.ensure_object(dict)
        ctx.obj["filter_order"] = filter_order
        return ctx


PARSER_MAP: dict[str, type[JsonParser | YamlParser]] = {
    "json": JsonParser,
    "yaml": YamlParser,
}


def _build_filters(
    builder: PipelineBuilder,
    filter_order: list[tuple[str, str]],
) -> ConfigurationError:
    """Add filters to the pipeline builder.

    Args:
        builder: Pipeline builder to add filters to.
        filter_order: List of (filter_type, value) tuples.

    Returns:
        ConfigurationError with any validation errors (empty if none).
    """
    errors = ConfigurationError()
    for i, (filter_type, value) in enumerate(filter_order):
        try:
            if filter_type == "include":
                builder.add_filter(IncludeFilter(value))
            elif filter_type == "exclude":
                builder.add_filter(ExcludeFilter(value))
            elif filter_type == "depth":
                builder.add_filter(MaxDepthFilter(int(value)))
        except ValueError as e:
            location = f"--{filter_type}[{i}]" if filter_type != "depth" else "--max-depth"
            errors.add(location, str(e))
    return errors


@click.command(cls=OrderedCommand)
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
    help="Include only paths matching dpath pattern. Can be repeated.",
)
@click.option(
    "--exclude",
    "-e",
    "exclude_patterns",
    multiple=True,
    help="Exclude paths matching dpath pattern. Can be repeated.",
)
@click.option(
    "--max-depth",
    "-d",
    "max_depth",
    type=int,
    help="Maximum depth to traverse.",
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
@click.argument(
    "input_file",
    type=click.Path(path_type=Path),
    required=False,
)
@click.pass_context
def main(
    ctx: click.Context,
    output_format: str,
    input_format: str,
    include_patterns: tuple[str, ...],  # noqa: ARG001
    exclude_patterns: tuple[str, ...],  # noqa: ARG001
    max_depth: int | None,  # noqa: ARG001
    output_file: Path | None,
    sort_keys: bool,  # noqa: FBT001
    no_color: bool,  # noqa: ARG001, FBT001
    input_file: Path | None,
) -> None:
    """Convert JSON/YAML/XML to token-efficient formats for LLM contexts.

    Supports TOON, compact JSON, and YAML output formats.
    Reduces token consumption by 30-60% when passing structured data to LLMs.

    Filters are applied in the order specified on the command line.
    """
    # Read input
    if input_file is None or str(input_file) == "-":
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

    # Add filters in CLI order
    filter_order = ctx.obj.get("filter_order", [])
    errors = _build_filters(builder, filter_order)
    if errors:
        raise click.ClickException(str(errors))

    # Run pipeline
    try:
        pipeline = builder.build()
        result = pipeline.run(data)

        # Output to file or stdout
        if output_file:
            output_file.write_text(result)
            click.echo(f"Written to {output_file}", err=True)
        else:
            click.echo(result, nl=False)
    except ParseError as e:
        msg = f"Parse error: {e}"
        raise click.ClickException(msg) from e
    except EncodeError as e:
        msg = f"Encode error: {e}"
        raise click.ClickException(msg) from e


if __name__ == "__main__":
    main()
