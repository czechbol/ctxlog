"""Tests for the Logger class."""

import io
from unittest.mock import patch

import pytest

import ctxlog
from ctxlog import Logger, LogLevel
from ctxlog.log import Log


def test_logger_init():
    """Test Logger initialization."""
    logger = Logger("test_module")
    assert logger.name == "test_module"


def test_logger_new():
    """Test Logger.new() method."""
    logger = Logger("test_module")
    log = logger.new()
    assert isinstance(log, Log)
    assert log.event == "test_module"


def test_logger_with_context():
    """Test creating a logger with context."""
    logger = Logger("test_module")
    log = logger.new()
    log.ctx(user_id="123", action="login")
    assert isinstance(log, Log)
    assert log.event == "test_module"

    # Check context fields through the log entry
    entry = log._build_log_entry(level=LogLevel.INFO)
    assert entry["user_id"] == "123"
    assert entry["action"] == "login"


def test_logger_with_custom_event():
    """Test creating a logger with a custom event."""
    logger = Logger("test_module")
    log = logger.new()
    log.event = "custom_event"
    log.ctx(user_id="123")
    assert isinstance(log, Log)
    assert log.event == "custom_event"

    # Check context fields through the log entry
    entry = log._build_log_entry(level=LogLevel.INFO)
    assert entry["user_id"] == "123"


def test_logger_with_debug_context():
    """Test creating a logger with DEBUG level context."""
    logger = Logger("test_module")
    log = logger.new()
    log.ctx(level=LogLevel.DEBUG, request_id="abc123")
    assert isinstance(log, Log)

    # Check that the debug context fields are included in the log entry
    log.level = LogLevel.DEBUG
    entry = log._build_log_entry(level=LogLevel.DEBUG)
    assert entry["request_id"] == "abc123"


def test_logger_with_error_context():
    """Test creating a logger with ERROR level context."""
    logger = Logger("test_module")
    log = logger.new()
    log.ctx(level=LogLevel.ERROR, error_code="E123")
    assert isinstance(log, Log)

    # Check that the error context fields are included in the log entry
    log.level = LogLevel.ERROR
    entry = log._build_log_entry(level=LogLevel.ERROR)
    assert entry["error_code"] == "E123"


def test_logger_with_exception():
    """Test creating a logger with an exception."""
    logger = Logger("test_module")
    log = logger.new()
    exception = ValueError("Test error")
    log.exc(exception)
    assert isinstance(log, Log)
    assert log.exception_info is not None
    assert log.exception_info["type"] == "ValueError"
    assert log.exception_info["value"] == "Test error"


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


@pytest.fixture
def mock_stdout():
    """Fixture to capture stdout."""
    buffer = io.StringIO()
    with patch("sys.stdout", buffer):
        yield buffer
        buffer.seek(0)  # Reset buffer position for reading


def test_logger_log_methods(mock_stdout):
    """Test Logger log methods (debug, info, warning, error, critical)."""
    # Create a mock handler to capture the logs with DEBUG level
    mock_handler = MockHandler(level=LogLevel.DEBUG)

    # Configure ctxlog with our mock handler
    ctxlog.configure(level=LogLevel.DEBUG, handlers=[mock_handler])

    logger = Logger("test_module")

    # Test each log method
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    # Check that logs were emitted
    assert len(mock_handler.logs) == 5

    # Check debug log
    assert mock_handler.logs[0]["level"] == "debug"
    assert mock_handler.logs[0]["message"] == "Debug message"

    # Check info log
    assert mock_handler.logs[1]["level"] == "info"
    assert mock_handler.logs[1]["message"] == "Info message"

    # Check warning log
    assert mock_handler.logs[2]["level"] == "warning"
    assert mock_handler.logs[2]["message"] == "Warning message"

    # Check error log
    assert mock_handler.logs[3]["level"] == "error"
    assert mock_handler.logs[3]["message"] == "Error message"

    # Check critical log
    assert mock_handler.logs[4]["level"] == "critical"
    assert mock_handler.logs[4]["message"] == "Critical message"


def test_get_logger():
    """Test get_logger function."""
    logger = ctxlog.get_logger("test_module")
    assert isinstance(logger, Logger)
    assert logger.name == "test_module"
