"""Tests for the Log class."""

import io
from unittest.mock import patch

import pytest

import ctxlog
from ctxlog import LogLevel
from ctxlog.log import Log, LogContext


def test_log_init():
    """Test Log initialization."""
    log = Log(event="test_event")
    assert log.level is None
    assert log.event == "test_event"

    assert log._context.__dict__ == LogContext().__dict__
    assert log._has_parent is False
    assert log.children == []
    assert log.message is None
    assert log.start_time is not None


def test_log_ctx():
    """Test Log.ctx() method."""
    log = Log(event="test_event")
    result = log.ctx(user_id="123", action="login")

    # Test method chaining
    assert result is log

    # Test context fields through the log entry
    log.level = LogLevel.INFO
    entry = log._build_log_entry(level=LogLevel.INFO)
    assert entry["user_id"] == "123"
    assert entry["action"] == "login"


def test_log_debug_ctx():
    """Test Log.ctx() method with DEBUG level."""
    log = Log(event="test_event")
    result = log.ctx(
        level=LogLevel.DEBUG, request_id="abc123", payload={"key": "value"}
    )

    # Test method chaining
    assert result is log

    # Test debug context fields are included in the log entry
    log.level = LogLevel.DEBUG
    entry = log._build_log_entry(level=LogLevel.DEBUG)
    assert entry["request_id"] == "abc123"
    assert entry["payload"] == {"key": "value"}


def test_log_error_ctx():
    """Test Log.ctx() method with ERROR level."""
    log = Log(event="test_event")
    result = log.ctx(level=LogLevel.ERROR, error_code="E123", details="Invalid input")

    # Test method chaining
    assert result is log

    # Test error context fields are included in the log entry
    log.level = LogLevel.ERROR  # Set log level to ERROR to include error fields
    entry = log._build_log_entry(level=LogLevel.ERROR)
    assert entry["error_code"] == "E123"
    assert entry["details"] == "Invalid input"


def test_log_exc():
    """Test Log.exc() method."""
    log = Log(event="test_event")
    exception = ValueError("Test error")
    result = log.exc(exception)

    # Test method chaining
    assert result is log

    # Test exception info
    assert log.exception_info is not None
    assert log.exception_info["type"] == "ValueError"
    assert log.exception_info["value"] == "Test error"
    assert "Traceback" in log.exception_info["traceback"]


def test_log_new():
    """Test Log.new() method for chaining."""
    parent_log = Log(event="parent_event")
    parent_log.ctx(request_id="123")
    child_log = parent_log.new(event="child_event")
    child_log.ctx(user_id="456")

    # Test parent-child relationship
    assert child_log in parent_log.children

    # Test child log properties
    assert child_log.event == "child_event"

    # Check context fields through the log entry
    child_log.level = LogLevel.INFO
    entry = child_log._build_log_entry(level=LogLevel.INFO)
    assert entry["user_id"] == "456"


def test_log_build_entry():
    """Test Log._build_log_entry method."""
    log = Log(event="test_event")
    log.level = LogLevel.INFO
    log.ctx(user_id="123", action="login")
    log.ctx(level=LogLevel.DEBUG, request_id="abc123")
    log.ctx(level=LogLevel.ERROR, error_code="E123")
    log.message = "Test message"

    # Build entry with INFO level
    entry = log._build_log_entry(level=LogLevel.INFO)
    assert entry["level"] == "info"
    assert entry["event"] == "test_event"
    assert entry["message"] == "Test message"
    assert entry["user_id"] == "123"
    assert entry["action"] == "login"
    assert "request_id" in entry  # Debug context is included (DEBUG < INFO)
    assert "error_code" not in entry  # Error context is not included (ERROR > INFO)

    # Build entry with DEBUG level
    entry = log._build_log_entry(level=LogLevel.DEBUG)
    assert entry["request_id"] == "abc123"  # Debug context included

    # Test error level includes error context
    log.level = LogLevel.ERROR
    entry = log._build_log_entry(level=LogLevel.ERROR)
    assert entry["error_code"] == "E123"  # Error context included


def test_log_build_entry_with_exception():
    """Test Log._build_log_entry with exception info."""
    log = Log(event="test_event")
    log.level = LogLevel.ERROR
    exception = ValueError("Test error")
    log.exc(exception)

    entry = log._build_log_entry(level=LogLevel.ERROR)
    assert "exception" in entry
    assert entry["exception"]["type"] == "ValueError"
    assert entry["exception"]["value"] == "Test error"


def test_log_build_entry_with_children():
    """Test Log._build_log_entry with child logs."""
    parent = Log(event="parent_event")
    parent.level = LogLevel.INFO
    child1 = parent.new(event="child1_event")
    child1.message = "Child 1 message"
    child1.level = LogLevel.INFO
    child2 = parent.new(event="child2_event")
    child2.message = "Child 2 message"
    child2.level = LogLevel.INFO

    entry = parent._build_log_entry(level=LogLevel.INFO)
    assert "children" in entry
    assert len(entry["children"]) == 2
    assert entry["children"][0]["event"] == "child1_event"
    assert entry["children"][0]["message"] == "Child 1 message"
    assert entry["children"][1]["event"] == "child2_event"
    assert entry["children"][1]["message"] == "Child 2 message"


@pytest.fixture
def mock_stdout():
    """Fixture to capture stdout."""
    buffer = io.StringIO()
    with patch("sys.stdout", buffer):
        yield buffer
        buffer.seek(0)  # Reset buffer position for reading


def test_log_emit(mock_stdout):
    """Test Log._emit method."""
    # Create a mock handler to capture the emitted log
    mock_handler = MockHandler()

    # Configure ctxlog with our mock handler
    ctxlog.configure(handlers=[mock_handler])

    log = Log(event="test_event")
    log.ctx(user_id="123")
    log._emit("Test message", LogLevel.INFO)

    # Check that the log was emitted to our mock handler
    assert len(mock_handler.logs) == 1
    log_entry = mock_handler.logs[0]
    assert log_entry["level"] == "info"
    assert log_entry["event"] == "test_event"
    assert log_entry["message"] == "Test message"
    assert log_entry["user_id"] == "123"
    assert "timestamp" in log_entry


def test_log_emit_chained_logs():
    """Test that chained logs don't emit directly."""
    # Configure ctxlog with a mock handler
    mock_handler = MockHandler()
    ctxlog.configure(handlers=[mock_handler])

    parent = Log(event="parent_event")
    child = parent.new(event="child_event")

    # Child log shouldn't emit
    child._emit("Child message", LogLevel.INFO)
    assert len(mock_handler.logs) == 0

    # Parent log should emit and include child
    parent._emit("Parent message", LogLevel.INFO)
    assert len(mock_handler.logs) == 1
    assert mock_handler.logs[0]["event"] == "parent_event"
    assert mock_handler.logs[0]["message"] == "Parent message"
    assert mock_handler.logs[0]["children"][0]["event"] == "child_event"
    assert mock_handler.logs[0]["children"][0]["message"] == "Child message"


def test_log_level_methods():
    """Test Log level methods (debug, info, warning, error, critical)."""
    # Configure ctxlog with a mock handler that accepts DEBUG level
    mock_handler = MockHandler(level=LogLevel.DEBUG)
    ctxlog.configure(level=LogLevel.DEBUG, handlers=[mock_handler])

    log = Log(event="test_event")

    # Test each method
    log.debug("Debug message")
    assert mock_handler.logs[-1]["level"] == "debug"
    assert mock_handler.logs[-1]["message"] == "Debug message"

    log = Log(event="test_event")
    log.info("Info message")
    assert mock_handler.logs[-1]["level"] == "info"
    assert mock_handler.logs[-1]["message"] == "Info message"

    log = Log(event="test_event")
    log.warning("Warning message")
    assert mock_handler.logs[-1]["level"] == "warning"
    assert mock_handler.logs[-1]["message"] == "Warning message"

    log = Log(event="test_event")
    log.error("Error message")
    assert mock_handler.logs[-1]["level"] == "error"
    assert mock_handler.logs[-1]["message"] == "Error message"

    log = Log(event="test_event")
    log.critical("Critical message")
    assert mock_handler.logs[-1]["level"] == "critical"
    assert mock_handler.logs[-1]["message"] == "Critical message"


# Helper class for testing
class MockHandler:
    """Mock handler for testing."""

    def __init__(self, level=None):
        self.logs = []
        self.level = level
        self.serialize = False

    def emit(self, log_entry):
        """Store the log entry."""
        self.logs.append(log_entry)
