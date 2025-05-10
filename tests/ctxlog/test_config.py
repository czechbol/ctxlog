"""Tests for the configuration module in __init__.py."""

import pytest

import ctxlog
from ctxlog import LogLevel
from ctxlog.handlers import ConsoleHandler, FileHandler


def test_default_config():
    """Test default configuration."""
    # Reset configuration to default
    ctxlog._global_config.level = LogLevel.INFO
    ctxlog._global_config.timefmt = "iso"
    ctxlog._global_config.utc = False
    ctxlog._global_config.handlers = [ConsoleHandler()]

    # Check default values
    assert ctxlog._global_config.level == LogLevel.INFO
    assert ctxlog._global_config.timefmt == "iso"
    assert not ctxlog._global_config.utc
    assert len(ctxlog._global_config.handlers) == 1
    assert isinstance(ctxlog._global_config.handlers[0], ConsoleHandler)


def test_configure_level():
    """Test configure with different level types."""
    # Test with LogLevel enum
    ctxlog.configure(level=LogLevel.DEBUG)
    assert ctxlog._global_config.level == LogLevel.DEBUG

    # Test with string
    ctxlog.configure(level="info")
    assert ctxlog._global_config.level == LogLevel.INFO

    # Test with uppercase string
    ctxlog.configure(level="WARNING")
    assert ctxlog._global_config.level == LogLevel.WARNING

    # Test with int (exact match)
    ctxlog.configure(level=40)  # ERROR
    assert ctxlog._global_config.level == LogLevel.ERROR

    # Test with int (invalid)
    with pytest.raises(ValueError):
        ctxlog.configure(level=100)

    # Test with invalid string
    with pytest.raises(ValueError):
        ctxlog.configure(level="invalid")

    # Test with invalid type
    with pytest.raises(TypeError):
        ctxlog.configure(level=3.14)


def test_configure_timefmt():
    """Test configure with different time formats."""
    ctxlog.configure(timefmt="iso")
    assert ctxlog._global_config.timefmt == "iso"

    ctxlog.configure(timefmt="%Y-%m-%d %H:%M:%S")
    assert ctxlog._global_config.timefmt == "%Y-%m-%d %H:%M:%S"


def test_configure_handlers():
    """Test configure with different handlers."""
    # Test with no handlers (should use default)
    ctxlog.configure(handlers=None)
    assert len(ctxlog._global_config.handlers) == 1
    assert isinstance(ctxlog._global_config.handlers[0], ConsoleHandler)

    # Test with custom handlers
    console_handler = ConsoleHandler(serialize=True)
    file_handler = FileHandler(file_path="test.log")
    ctxlog.configure(handlers=[console_handler, file_handler])

    assert len(ctxlog._global_config.handlers) == 2
    assert ctxlog._global_config.handlers[0] is console_handler
    assert ctxlog._global_config.handlers[1] is file_handler


def test_configure_full():
    """Test configure with all parameters."""
    console_handler = ConsoleHandler(serialize=True)
    file_handler = FileHandler(file_path="test.log")

    ctxlog.configure(
        level=LogLevel.WARNING,
        timefmt="%Y-%m-%d",
        handlers=[console_handler, file_handler],
    )

    assert ctxlog._global_config.level == LogLevel.WARNING
    assert ctxlog._global_config.timefmt == "%Y-%m-%d"
    assert len(ctxlog._global_config.handlers) == 2
    assert ctxlog._global_config.handlers[0] is console_handler
    assert ctxlog._global_config.handlers[1] is file_handler
