"""Tests for the LogLevel class."""

import pytest

from ctxlog.level import LogLevel


def test_log_level_values():
    """Test that log level values are in ascending order."""
    assert LogLevel.DEBUG.value < LogLevel.INFO.value
    assert LogLevel.INFO.value < LogLevel.WARNING.value
    assert LogLevel.WARNING.value < LogLevel.ERROR.value
    assert LogLevel.ERROR.value < LogLevel.CRITICAL.value


def test_log_level_from_string():
    """Test converting strings to LogLevel."""
    assert LogLevel.from_string("debug") == LogLevel.DEBUG
    assert LogLevel.from_string("DEBUG") == LogLevel.DEBUG
    assert LogLevel.from_string("info") == LogLevel.INFO
    assert LogLevel.from_string("warning") == LogLevel.WARNING
    assert LogLevel.from_string("error") == LogLevel.ERROR
    assert LogLevel.from_string("critical") == LogLevel.CRITICAL


def test_log_level_from_string_invalid():
    """Test that invalid strings raise ValueError."""
    with pytest.raises(ValueError):
        LogLevel.from_string("invalid")


def test_log_level_str():
    """Test string representation of LogLevel."""
    assert str(LogLevel.DEBUG) == "debug"
    assert str(LogLevel.INFO) == "info"
    assert str(LogLevel.WARNING) == "warning"
    assert str(LogLevel.ERROR) == "error"
    assert str(LogLevel.CRITICAL) == "critical"
