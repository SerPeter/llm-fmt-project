# Task 006: CLI Interface (Click)

**Phase**: 1 - MVP  
**Priority**: +200
**Storypoints**: 5  
**Status**: [ ] Not started

## Objective

Build the command-line interface using Click with intuitive UX and shell completion support.

## Requirements

- [ ] Main `llm-fmt` command with subcommands or flags
- [ ] `--format` option for output format selection
- [ ] `--output` option for file output (default: stdout)
- [ ] `--help` with clear usage examples
- [ ] Exit codes: 0 success, 1 error, 2 invalid input
- [ ] Color output for terminals (disable with `--no-color`)

## Implementation Details

### Main CLI Module

```python
# src/llm_fmt/cli.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from llm_fmt.convert import convert
from llm_fmt.parsers import parse_input


FORMATS = ["toon", "compact-json", "yaml", "tsv", "auto"]


@click.command()
@click.argument("input", type=click.Path(exists=True, allow_dash=True), default="-")
@click.option(
    "-f", "--format",
    type=click.Choice(FORMATS, case_sensitive=False),
    default="auto",
    help="Output format (default: auto-detect optimal)"
)
@click.option(
    "-o", "--output",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file (default: stdout)"
)
@click.option(
    "--filter",
    "filter_path",
    help="dpath glob pattern to filter data"
)
@click.option(
    "--max-depth",
    type=int,
    help="Maximum nesting depth to include"
)
@click.option(
    "--exclude",
    help="Comma-separated field names to exclude"
)
@click.option(
    "--analyze",
    is_flag=True,
    help="Show token analysis for all formats"
)
@click.option(
    "--sort-keys",
    is_flag=True,
    help="Sort object keys alphabetically"
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output"
)
@click.version_option()
def main(
    input: str,
    format: str,
    output: Optional[str],
    filter_path: Optional[str],
    max_depth: Optional[int],
    exclude: Optional[str],
    analyze: bool,
    sort_keys: bool,
    no_color: bool,
) -> None:
    """
    Convert JSON/YAML/XML to token-efficient formats for LLM consumption.
    
    \b
    Examples:
      llm-fmt data.json --format toon
      llm-fmt data.json --auto
      llm-fmt data.json --filter "users/*/email" --format toon
      cat api-response.json | llm-fmt --format compact-json
      llm-fmt large.json --analyze
    """
    try:
        # Parse input
        data = parse_input(input)
        
        # Apply filters
        if filter_path or max_depth or exclude:
            from llm_fmt.filter import apply_filters
            exclude_list = exclude.split(",") if exclude else []
            data = apply_filters(data, filter_path, max_depth, exclude_list)
        
        # Analysis mode
        if analyze:
            from llm_fmt.analyze import print_analysis
            print_analysis(data, no_color=no_color)
            return
        
        # Convert
        result = convert(data, format=format, sort_keys=sort_keys)
        
        # Output
        if output:
            Path(output).write_text(result)
            click.echo(f"Written to {output}", err=True)
        else:
            click.echo(result)
            
    except Exception as e:
        click.secho(f"Error: {e}", fg="red" if not no_color else None, err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Shell Completion

Click supports automatic shell completion:

```bash
# Bash
eval "$(_LLM_FMT_COMPLETE=bash_source llm-fmt)"

# Zsh
eval "$(_LLM_FMT_COMPLETE=zsh_source llm-fmt)"

# Fish
_LLM_FMT_COMPLETE=fish_source llm-fmt | source
```

Add to README with installation instructions.

### Error Messages

```python
# Good error messages
"Error: File not found: input.json"
"Error: Invalid JSON at line 15, column 8: Unexpected token"
"Error: Unknown format 'toml'. Choose from: toon, compact-json, yaml, tsv, auto"
```

## Acceptance Criteria

- [ ] `llm-fmt --help` shows clear usage
- [ ] `llm-fmt input.json` works (default format)
- [ ] `llm-fmt input.json -f toon` converts to TOON
- [ ] `llm-fmt - < input.json` reads from stdin
- [ ] `llm-fmt input.json -o out.toon` writes to file
- [ ] Invalid input shows helpful error message
- [ ] `--version` shows package version

## Test Cases

```python
from click.testing import CliRunner
from llm_fmt.cli import main

def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Convert JSON" in result.output

def test_basic_conversion(tmp_path):
    input_file = tmp_path / "test.json"
    input_file.write_text('{"key": "value"}')
    
    runner = CliRunner()
    result = runner.invoke(main, [str(input_file), "-f", "compact-json"])
    assert result.exit_code == 0
    assert '{"key":"value"}' in result.output

def test_stdin():
    runner = CliRunner()
    result = runner.invoke(main, ["-"], input='{"test": 1}')
    assert result.exit_code == 0
```

## Dependencies

- `click>=8.1`

## Notes

- Click handles terminal detection, colors, and pagination
- Use `click.echo()` instead of `print()` for proper stream handling
- `allow_dash=True` enables `-` to mean stdin
- Consider adding `--quiet` flag for scripts
