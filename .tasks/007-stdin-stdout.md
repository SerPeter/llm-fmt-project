# Task 007: Stdin/Stdout Piping

**Phase**: 1 - MVP  
**Priority**: +150
**Storypoints**: 2  
**Status**: [ ] Not started

## Objective

Ensure robust stdin/stdout handling for shell pipeline usage.

## Requirements

- [ ] Read from stdin when no file argument or `-` provided
- [ ] Write to stdout by default
- [ ] Handle binary mode correctly for orjson
- [ ] Don't hang waiting for input when stdin is empty/TTY
- [ ] Proper encoding handling (UTF-8)

## Implementation Details

```python
# src/llm_fmt/io.py
import sys
from typing import BinaryIO, TextIO


def read_stdin_bytes() -> bytes:
    """Read all bytes from stdin."""
    if sys.stdin.isatty():
        raise ValueError("No input provided. Pipe data or specify a file.")
    return sys.stdin.buffer.read()


def read_stdin_text() -> str:
    """Read all text from stdin as UTF-8."""
    return read_stdin_bytes().decode("utf-8")


def write_stdout(content: str | bytes) -> None:
    """Write content to stdout."""
    if isinstance(content, bytes):
        sys.stdout.buffer.write(content)
        sys.stdout.buffer.write(b"\n")
    else:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")
    sys.stdout.flush()


def is_pipe_input() -> bool:
    """Check if stdin has piped data."""
    return not sys.stdin.isatty()
```

### TTY Detection

Important for good UX:
- If stdin is a TTY (interactive terminal) and no file given, show help
- If stdin is a pipe, read from it

```python
@click.command()
@click.argument("input", required=False)
def main(input: str | None):
    if input is None:
        if sys.stdin.isatty():
            # No input and no pipe - show help
            click.echo(click.get_current_context().get_help())
            sys.exit(0)
        else:
            # Read from pipe
            data = read_stdin_bytes()
    else:
        # Read from file
        data = Path(input).read_bytes()
```

## Usage Patterns

```bash
# All these should work:
llm-fmt input.json                    # File argument
llm-fmt input.json -f toon            # With format
cat input.json | llm-fmt              # Piped input
cat input.json | llm-fmt -f toon      # Piped with format
llm-fmt - < input.json                # Explicit stdin
llm-fmt < input.json                  # Redirect (might need -)
echo '{"a":1}' | llm-fmt              # Inline JSON

# Output redirection
llm-fmt input.json > output.toon      # Redirect stdout
llm-fmt input.json -o output.toon     # Explicit output file
llm-fmt input.json | head -n 10       # Pipe to other tools
```

## Acceptance Criteria

- [ ] `cat file.json | llm-fmt` works
- [ ] `llm-fmt` without args shows help (not hang)
- [ ] `llm-fmt - < file.json` reads from stdin
- [ ] Output to stdout doesn't include extra newlines
- [ ] UTF-8 content preserved correctly
- [ ] Binary stdin mode works with orjson

## Test Cases

```python
def test_stdin_pipe(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, input='{"test": 1}')
    assert result.exit_code == 0

def test_no_input_shows_help():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert "Usage:" in result.output or result.exit_code == 0

def test_stdout_encoding():
    # Test with unicode characters
    runner = CliRunner()
    result = runner.invoke(main, input='{"emoji": "🎉"}')
    assert "🎉" in result.output
```

## Notes

- Click's `CliRunner` simulates stdin for testing
- `sys.stdin.buffer` gives raw bytes, `sys.stdin` gives text
- Consider `--input-encoding` flag for non-UTF-8 files (later)
- Large files: may need streaming instead of `read()`
