"""Tests for the formatting functionality in handlers module."""

import json

from ctxlog.handlers import ConsoleHandler, Handler


# Create a concrete implementation of the abstract Handler class for testing
class ConcreteHandler(Handler):
    """Concrete implementation of the abstract Handler class for testing."""

    def emit(self, log_entry):
        """Implement the abstract emit method."""
        pass


def test_handler_format_nested_children():
    """Test Handler.format with deeply nested children."""
    handler = ConcreteHandler(serialize=False)

    # Create a log entry with deeply nested children
    log_entry = {
        "timestamp": "2023-01-01T00:00:00Z",
        "level": "info",
        "event": "parent_event",
        "message": "Parent message",
        "children": [
            {
                "level": "info",
                "event": "child_event",
                "message": "Child message",
                "user_id": "123",
                "children": [
                    {
                        "level": "warning",
                        "event": "grandchild_event",
                        "message": "Grandchild message",
                        "request_id": "456",
                        "children": [
                            {
                                "level": "error",
                                "event": "great_grandchild_event",
                                "message": "Great-grandchild message",
                            }
                        ],
                    }
                ],
            },
            {
                "level": "debug",
                "event": "second_child_event",
                "message": "Second child message",
            },
        ],
    }

    formatted = handler.format(log_entry)

    # Check that all levels of nesting are included
    assert "parent_event: Parent message" in formatted
    assert "[INFO] child_event: Child message" in formatted
    assert "user_id=123" in formatted
    assert "[WARNING] grandchild_event: Grandchild message" in formatted
    assert "request_id=456" in formatted
    assert "[ERROR] great_grandchild_event: Great-grandchild message" in formatted
    assert "[DEBUG] second_child_event: Second child message" in formatted

    # Check indentation levels
    lines = formatted.split("\n")
    assert any(line.startswith("  [INFO]") for line in lines)  # Level 1 indentation
    assert any(
        line.startswith("    [WARNING]") for line in lines
    )  # Level 2 indentation
    assert any(
        line.startswith("      [ERROR]") for line in lines
    )  # Level 3 indentation


def test_handler_format_with_nested_exceptions():
    """Test Handler.format with exceptions in nested children."""
    handler = ConcreteHandler(serialize=False)

    # Create a log entry with exceptions in nested children
    log_entry = {
        "timestamp": "2023-01-01T00:00:00Z",
        "level": "error",
        "event": "parent_event",
        "message": "Parent message",
        "exception": {
            "type": "ValueError",
            "value": "Parent error",
            "traceback": 'Traceback (most recent call last):\n  File "parent.py", line 10, in parent_func\n    raise ValueError("Parent error")',
        },
        "children": [
            {
                "level": "error",
                "event": "child_event",
                "message": "Child message",
                "exception": {
                    "type": "TypeError",
                    "value": "Child error",
                    "traceback": 'Traceback (most recent call last):\n  File "child.py", line 5, in child_func\n    raise TypeError("Child error")',
                },
            },
        ],
    }

    formatted = handler.format(log_entry)

    # Check that parent exception is included
    assert "Exception: ValueError: Parent error" in formatted
    assert 'File "parent.py", line 10' in formatted

    # Check that child exception is included with proper indentation
    assert "  Exception: TypeError: Child error" in formatted
    assert '  File "child.py", line 5' in formatted


def test_handler_format_with_complex_context():
    """Test Handler.format with complex context fields."""
    handler = ConcreteHandler(serialize=False)

    # Create a log entry with complex context fields
    log_entry = {
        "timestamp": "2023-01-01T00:00:00Z",
        "level": "info",
        "event": "test_event",
        "message": "Test message",
        "user_id": "123",
        "request_id": "456",
        "metadata": {"key1": "value1", "key2": "value2"},
        "tags": ["tag1", "tag2", "tag3"],
        "count": 42,
        "is_valid": True,
    }

    formatted = handler.format(log_entry)

    # Check that all context fields are included
    assert "user_id=123" in formatted
    assert "request_id=456" in formatted
    assert "metadata={'key1': 'value1', 'key2': 'value2'}" in formatted
    assert "tags=['tag1', 'tag2', 'tag3']" in formatted
    assert "count=42" in formatted
    assert "is_valid=True" in formatted


def test_handler_format_serialized_with_complex_data():
    """Test Handler.format with serialization and complex data."""
    handler = ConcreteHandler(serialize=True)

    # Create a log entry with complex data
    log_entry = {
        "timestamp": "2023-01-01T00:00:00Z",
        "level": "info",
        "event": "test_event",
        "message": "Test message",
        "user_id": "123",
        "metadata": {"key1": "value1", "key2": "value2"},
        "tags": ["tag1", "tag2", "tag3"],
        "nested": {"level1": {"level2": {"level3": "deep_value"}}},
        "children": [
            {
                "level": "debug",
                "message": "Child message",
            }
        ],
    }

    formatted = handler.format(log_entry)

    # Parse the JSON to verify it's valid
    parsed = json.loads(formatted)

    # Check that all fields are included and in the correct order
    keys = list(parsed.keys())
    # The first keys should be in the specified order if present
    expected_order = [
        "timestamp",
        "level",
        "event",
        "message",
        "ctx_start",
    ]
    # All expected_order keys that are present should be in the correct order
    last_index = -1
    for key in expected_order:
        if key in keys:
            idx = keys.index(key)
            assert idx > last_index, (
                f"Key '{key}' is out of order in serialized log: {keys}"
            )
            last_index = idx
    # Children and exception should be last if present
    if "children" in keys:
        assert keys[-2] == "children" or keys[-1] == "children"
    if "exception" in keys:
        assert keys[-1] == "exception" or (
            "children" in keys and keys[-2] == "exception"
        )

    # Check that all fields are included
    assert parsed["timestamp"] == "2023-01-01T00:00:00Z"
    assert parsed["level"] == "info"
    assert parsed["event"] == "test_event"
    assert parsed["message"] == "Test message"
    assert parsed["user_id"] == "123"
    assert parsed["metadata"] == {"key1": "value1", "key2": "value2"}
    assert parsed["tags"] == ["tag1", "tag2", "tag3"]
    assert parsed["nested"]["level1"]["level2"]["level3"] == "deep_value"
    assert parsed["children"][0]["level"] == "debug"
    assert parsed["children"][0]["message"] == "Child message"


def test_console_handler_format_with_no_event():
    """Test ConsoleHandler.format with no event field."""
    handler = ConsoleHandler(serialize=False)

    # Create a log entry without an event field
    log_entry = {
        "timestamp": "2023-01-01T00:00:00Z",
        "level": "info",
        "message": "Test message without event",
        "user_id": "123",
    }

    formatted = handler.format(log_entry)

    # Check that the format is correct without an event
    assert "2023-01-01T00:00:00Z [INFO] Test message without event" in formatted
    assert "user_id=123" in formatted


def test_console_handler_format_with_empty_fields():
    """Test ConsoleHandler.format with empty or missing fields."""
    handler = ConsoleHandler(serialize=False)

    # Create a log entry with empty or missing fields
    log_entry = {
        "level": "info",
        "message": "Test message with missing fields",
    }

    formatted = handler.format(log_entry)

    # Check that the format handles missing fields
    assert "[INFO] Test message with missing fields" in formatted
    assert "timestamp" not in formatted  # No timestamp in output


def test_handler_format_child_with_no_event():
    """Test Handler._format_child with no event field."""
    handler = ConcreteHandler(serialize=False)

    # Create a child log entry without an event field
    child = {
        "level": "info",
        "message": "Child message without event",
        "user_id": "123",
    }

    formatted = handler._format_child(child, indent_level=1)

    # Check that the format is correct without an event
    assert "  [INFO] Child message without event" in formatted
    assert "user_id=123" in formatted


def test_handler_format_child_with_nested_children():
    """Test Handler._format_child with nested children."""
    handler = ConcreteHandler(serialize=False)

    # Create a child log entry with nested children
    child = {
        "level": "info",
        "event": "child_event",
        "message": "Child message",
        "children": [
            {
                "level": "debug",
                "event": "grandchild_event",
                "message": "Grandchild message",
            }
        ],
    }

    formatted = handler._format_child(child, indent_level=1)

    # Check that the child and its children are formatted correctly
    assert "  [INFO] child_event: Child message" in formatted
    assert "    [DEBUG] grandchild_event: Grandchild message" in formatted
