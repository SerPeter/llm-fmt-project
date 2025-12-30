"""Tests for error types."""

from llm_fmt.errors import (
    ConfigError,
    ConfigurationError,
    EncodeError,
    FilterError,
    InputError,
    LLMFmtError,
    OutputError,
    ParseError,
    ValidationError,
)


class TestValidationError:
    """Tests for ValidationError class."""

    def test_str_format(self) -> None:
        """Validation error formats as location: message."""
        error = ValidationError("--filter[0]", "Invalid pattern")
        assert str(error) == "--filter[0]: Invalid pattern"


class TestConfigurationError:
    """Tests for ConfigurationError class."""

    def test_empty_errors_str(self) -> None:
        """Empty error list produces empty string."""
        error = ConfigurationError()
        assert str(error) == ""

    def test_single_error_str(self) -> None:
        """Single error formats correctly."""
        error = ConfigurationError()
        error.add("--output", "Invalid path")
        assert str(error) == "--output: Invalid path"

    def test_multiple_errors_str(self) -> None:
        """Multiple errors format one per line."""
        error = ConfigurationError()
        error.add("--filter[0]", "Bad pattern")
        error.add("--max-depth", "Must be positive")
        assert str(error) == "--filter[0]: Bad pattern\n--max-depth: Must be positive"

    def test_add_returns_self(self) -> None:
        """Add method returns self for chaining."""
        error = ConfigurationError()
        result = error.add("--test", "message")
        assert result is error

    def test_bool_false_when_empty(self) -> None:
        """Empty error is falsy."""
        error = ConfigurationError()
        assert not error
        assert bool(error) is False

    def test_bool_true_when_has_errors(self) -> None:
        """Error with errors is truthy."""
        error = ConfigurationError()
        error.add("--test", "message")
        assert error
        assert bool(error) is True


class TestParseError:
    """Tests for ParseError class."""

    def test_str_without_source(self) -> None:
        """Error without source shows just message."""
        error = ParseError("Invalid JSON")
        assert str(error) == "Invalid JSON"

    def test_str_with_source(self) -> None:
        """Error with source prefixes message."""
        error = ParseError("Invalid JSON", source="input.json")
        assert str(error) == "input.json: Invalid JSON"


class TestEncodeError:
    """Tests for EncodeError class."""

    def test_str_without_format(self) -> None:
        """Error without format shows just message."""
        error = EncodeError("Cannot encode value")
        assert str(error) == "Cannot encode value"

    def test_str_with_format(self) -> None:
        """Error with format prefixes message."""
        error = EncodeError("Unsupported type", format_name="toon")
        assert str(error) == "toon: Unsupported type"


class TestLLMFmtError:
    """Tests for LLMFmtError base class."""

    def test_default_exit_code(self) -> None:
        """Base error has exit code 1."""
        error = LLMFmtError("test error")
        assert error.exit_code == 1

    def test_is_exception(self) -> None:
        """LLMFmtError is an Exception."""
        error = LLMFmtError("test")
        assert isinstance(error, Exception)


class TestExitCodes:
    """Tests for exit codes on all error types."""

    def test_parse_error_exit_code(self) -> None:
        """ParseError has exit code 2 (input error)."""
        error = ParseError("Invalid JSON")
        assert error.exit_code == 2

    def test_input_error_exit_code(self) -> None:
        """InputError has exit code 2."""
        error = InputError("File not found")
        assert error.exit_code == 2

    def test_config_error_exit_code(self) -> None:
        """ConfigError has exit code 2."""
        error = ConfigError("Invalid config")
        assert error.exit_code == 2

    def test_configuration_error_exit_code(self) -> None:
        """ConfigurationError has exit code 2."""
        error = ConfigurationError()
        assert error.exit_code == 2

    def test_encode_error_exit_code(self) -> None:
        """EncodeError has exit code 1."""
        error = EncodeError("Cannot encode")
        assert error.exit_code == 1

    def test_filter_error_exit_code(self) -> None:
        """FilterError has exit code 1."""
        error = FilterError("Invalid filter")
        assert error.exit_code == 1

    def test_output_error_exit_code(self) -> None:
        """OutputError has exit code 1."""
        error = OutputError("Cannot write")
        assert error.exit_code == 1


class TestErrorInheritance:
    """Tests for error inheritance from LLMFmtError."""

    def test_parse_error_inherits_base(self) -> None:
        """ParseError inherits from LLMFmtError."""
        assert issubclass(ParseError, LLMFmtError)

    def test_input_error_inherits_base(self) -> None:
        """InputError inherits from LLMFmtError."""
        assert issubclass(InputError, LLMFmtError)

    def test_config_error_inherits_base(self) -> None:
        """ConfigError inherits from LLMFmtError."""
        assert issubclass(ConfigError, LLMFmtError)

    def test_encode_error_inherits_base(self) -> None:
        """EncodeError inherits from LLMFmtError."""
        assert issubclass(EncodeError, LLMFmtError)

    def test_filter_error_inherits_base(self) -> None:
        """FilterError inherits from LLMFmtError."""
        assert issubclass(FilterError, LLMFmtError)

    def test_output_error_inherits_base(self) -> None:
        """OutputError inherits from LLMFmtError."""
        assert issubclass(OutputError, LLMFmtError)
