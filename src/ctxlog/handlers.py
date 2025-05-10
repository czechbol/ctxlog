import gzip
import json
import os
import sys
import threading
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import IO, Any, Dict, Literal, Optional

from .level import LogLevel


class FileRotation:
    """Configuration for log file rotation."""

    def __init__(
        self,
        size: Optional[str] = None,
        time: Optional[str] = None,
        keep: int = 5,
        compression: Optional[Literal["gzip", "zip"]] = None,
    ) -> None:
        """Initialize a FileRotation configuration.

        Args:
            size: Size threshold for rotation (e.g., "20MB"). Mutually exclusive with time.
            time: Time of day for rotation (e.g., "00.00"). Mutually exclusive with size.
            keep: Number of rotated files to keep.
            compression: Compression method for old files (e.g., "gzip", "zip").

        Raises:
            ValueError: If both size and time are specified.
        """
        if size is not None and time is not None:
            raise ValueError("Cannot specify both size and time for rotation")

        self.size = size
        self.time = time
        self.keep = keep
        self.compression = compression

    def should_rotate(self, file_path: Path) -> bool:
        """Check if the file should be rotated.

        Args:
            file_path: Path to the log file.

        Returns:
            True if the file should be rotated, False otherwise.
        """
        if not file_path.exists():
            return False

        if self.size is not None:
            # Parse size string (e.g., "20MB")
            size_str = self.size.lower()

            # Get the file size
            file_size = file_path.stat().st_size

            # Calculate max_bytes based on the size string
            if size_str.endswith("kb"):
                max_bytes = float(size_str[:-2]) * 1024
            elif size_str.endswith("mb"):
                max_bytes = float(size_str[:-2]) * 1024 * 1024
            elif size_str.endswith("gb"):
                max_bytes = float(size_str[:-2]) * 1024 * 1024 * 1024
            else:
                max_bytes = float(size_str)

            # Convert to integer for comparison
            max_bytes = int(max_bytes)

            return file_size >= max_bytes

        if self.time is not None:
            # Check if current time matches rotation time
            now = datetime.now()
            hour, minute = map(int, self.time.split("."))
            return now.hour == hour and now.minute == minute

        return False


class Handler(ABC):
    """Base class for log handlers."""

    def __init__(
        self,
        level: Optional[LogLevel] = None,
        serialize: bool = False,
    ) -> None:
        """Initialize a Handler.

        Args:
            level: Log level for this handler. If None, uses the global level.
            serialize: Whether to serialize logs as JSON.
        """
        self.level = level
        self.serialize = serialize
        self._lock = threading.Lock()  # Lock for thread safety

    @abstractmethod
    def emit(self, log_entry: Dict[str, Any]) -> None:
        """Emit a log entry.

        Args:
            log_entry: The log entry to emit.
        """
        pass

    def close(self) -> None:
        """Close any resources used by the handler."""
        pass

    def format(self, log_entry: Dict[str, Any]) -> str:
        """Format a log entry.

        Args:
            log_entry: The log entry to format.

        Returns:
            The formatted log entry.
        """
        if self.serialize:
            # Ensure the serialized JSON follows the specified order and exclude empty fields
            ordered_log_entry = {
                key: value
                for key, value in {
                    "timestamp": log_entry.get("timestamp", ""),
                    "level": log_entry.get("level", ""),  # Use original case
                    "event": log_entry.get("event", None),
                    "message": log_entry.get("message", ""),
                    "ctx_start": log_entry.get("ctx_start", None),
                    **{
                        key: value
                        for key, value in log_entry.items()
                        if key
                        not in [
                            "timestamp",
                            "level",
                            "event",
                            "message",
                            "ctx_start",
                            "children",
                            "exception",
                        ]
                    },
                    "children": log_entry.get("children", None),
                    "exception": log_entry.get("exception", None),
                }.items()
                if value not in (None, "", [])
            }
            return json.dumps(ordered_log_entry)

        # Human-readable format
        timestamp = log_entry.get("timestamp", "")
        level = log_entry.get("level", "").upper()
        event = log_entry.get("event", "")
        message = log_entry.get("message", "")

        # Format basic log line (without colors - they'll be added in emit if needed)
        if event:
            log_line = f"{timestamp} [{level}] {event}: {message}"
        else:
            log_line = f"{timestamp} [{level}] {message}"

        # Add context fields
        context_fields = []
        for key, value in log_entry.items():
            if key not in [
                "timestamp",
                "level",
                "event",
                "message",
                "children",
                "exception",
                "ctx_start",
            ]:
                context_fields.append(f"{key}={value}")

        if context_fields:
            log_line += " " + " ".join(context_fields)

        # Add exception if present
        if "exception" in log_entry:
            exc = log_entry["exception"]
            # Add deeper indentation to the exception line (one level deeper)
            log_line += f"\n  Exception: {exc.get('type')}: {exc.get('value')}"
            if "traceback" in exc:
                # Add indentation to each line of the traceback for better readability
                traceback_lines = exc["traceback"].split("\n")
                # Add one level of indentation to all traceback lines
                indented_traceback = "\n".join(
                    [f"  {line}" for line in traceback_lines]
                )
                log_line += f"\n{indented_traceback}"

        # Add children if present
        if "children" in log_entry and log_entry["children"]:
            for child in log_entry["children"]:
                log_line += "\n" + self._format_child(child, indent_level=1)

        return log_line

    def _format_child(self, child: Dict[str, Any], indent_level: int) -> str:
        """Format a child log entry recursively.

        Args:
            child: The child log entry to format.
            indent_level: The current indentation level.

        Returns:
            The formatted child log entry.
        """
        # Format the child log line with proper indentation
        indent = "  " * indent_level
        child_level = child.get("level", "").upper()
        child_event = child.get("event", "")
        child_message = child.get("message", "")

        # Format the child log line
        if child_event:
            child_line = f"{indent}[{child_level}] {child_event}: {child_message}"
        else:
            child_line = f"{indent}[{child_level}] {child_message}"

        # Add context fields for the child
        context_fields = []
        for key, value in child.items():
            if key not in [
                "timestamp",
                "level",
                "event",
                "message",
                "children",
                "exception",
                "ctx_start",
            ]:
                context_fields.append(f"{key}={value}")

        if context_fields:
            child_line += " " + " ".join(context_fields)

        # Add exception if present in the child
        if "exception" in child:
            exc = child["exception"]
            # Add deeper indentation to the exception line (one level deeper than the child log)
            child_line += (
                f"\n{indent}  Exception: {exc.get('type')}: {exc.get('value')}"
            )
            if "traceback" in exc:
                # Add indentation to each line of the traceback for better readability
                traceback_lines = exc["traceback"].split("\n")
                # Ensure consistent indentation for all traceback lines (one level deeper)
                indented_traceback = "\n".join(
                    [f"{indent}  {line}" for line in traceback_lines]
                )
                child_line += f"\n{indented_traceback}"

        # Recursively format any children of this child
        if "children" in child and child["children"]:
            for grandchild in child["children"]:
                child_line += "\n" + self._format_child(grandchild, indent_level + 1)

        return child_line


class ConsoleHandler(Handler):
    """Handler that outputs logs to the console."""

    def __init__(
        self,
        level: Optional[LogLevel] = None,
        serialize: bool = False,
        color: bool = True,
        use_stderr: bool = False,
    ) -> None:
        """Initialize a ConsoleHandler.

        Args:
            level: Log level for this handler. If None, uses the global level.
            serialize: Whether to serialize logs as JSON.
            color: Whether to use colored output (only applies if serialize=False).
            use_stderr: Whether to write logs to stderr instead of stdout.
        """
        super().__init__(level, serialize)
        self.color = color and not serialize  # Only use color if not serializing
        self.use_stderr = use_stderr
        # We don't need to open stdout/stderr as they're already open file objects

    def emit(self, log_entry: Dict[str, Any]) -> None:
        """Emit a log entry to the console.

        Args:
            log_entry: The log entry to emit.
        """
        # Get the formatted log line
        formatted = self.format(log_entry)

        if self.color and not self.serialize:
            # Apply selective coloring
            formatted = self._apply_selective_coloring(formatted, log_entry)

        # Use lock to prevent interleaved output from multiple threads
        with self._lock:
            if self.use_stderr and log_entry.get("level", "").lower() in [
                "warning",
                "error",
                "critical",
            ]:
                sys.stderr.write(formatted + "\n")
                sys.stderr.flush()  # Ensure immediate output
            else:
                sys.stdout.write(formatted + "\n")
                sys.stdout.flush()  # Ensure immediate output

    def _apply_selective_coloring(
        self, formatted: str, log_entry: Dict[str, Any]
    ) -> str:
        """Apply selective coloring to different parts of the log line.

        Args:
            formatted: The formatted log line.
            log_entry: The log entry.

        Returns:
            The formatted log line with selective coloring.
        """
        # Split the log entry into lines
        lines = formatted.split("\n")
        colored_lines = []

        # Process the main log line
        main_line = lines[0]
        level = log_entry.get("level", "").lower()
        colored_lines.append(self._color_log_line(main_line, level))

        # Process the rest of the lines
        i = 1
        while i < len(lines):
            line = lines[i]

            # Check if this is an exception line (could be at root or in child logs)
            if "Exception:" in line:
                # Apply color to the exception line (use error color)
                level_color = self._get_level_color("error")
                # Keep any indentation
                indent = ""
                if not line.startswith("Exception:"):
                    indent_end = line.find("Exception:")
                    indent = line[:indent_end]
                    line = line[indent_end:]

                parts = line.split(":", 2)
                if len(parts) >= 3:
                    exception_type = parts[1].strip()
                    exception_message = parts[2].strip()
                    colored_line = f"{indent}Exception: {level_color}{exception_type}:\033[0m {exception_message}"
                    colored_lines.append(colored_line)
                else:
                    colored_lines.append(line)  # Keep as is if can't parse

                i += 1
                # Add traceback lines with subtle coloring
                while i < len(lines) and not (
                    lines[i].lstrip().startswith("[")
                    or lines[i].startswith("Child logs:")
                ):
                    current_line = lines[i]
                    # Preserve indentation for child logs
                    current_indent = ""
                    if indent and current_line.startswith(indent):
                        current_indent = indent
                        current_line = current_line[len(indent) :]

                    # Add subtle coloring to traceback lines
                    if "Traceback (most recent call last):" in current_line:
                        colored_lines.append(
                            f"{current_indent}\033[90m{current_line}\033[0m"
                        )  # Gray for traceback header
                    elif "File " in current_line and ", line " in current_line:
                        # Highlight file paths in traceback
                        file_parts = current_line.split(", line ")
                        if len(file_parts) >= 2:
                            file_path = file_parts[0]
                            line_rest = ", line " + file_parts[1]
                            colored_lines.append(
                                f"{current_indent}\033[36m{file_path}\033[0m{line_rest}"
                            )  # Cyan for file paths
                    elif "Error:" in current_line or "Exception:" in current_line:
                        # Highlight error names
                        error_parts = current_line.split(":", 1)
                        if len(error_parts) >= 2:
                            error_name = error_parts[0]
                            error_msg = ":" + error_parts[1]
                            colored_lines.append(
                                f"{current_indent}{level_color}{error_name}\033[0m{error_msg}"
                            )
                    elif (
                        "The above exception was the direct cause of the following exception:"
                        in current_line
                    ):
                        # Highlight cause message
                        colored_lines.append(
                            f"{current_indent}\033[90m{current_line}\033[0m"
                        )  # Gray for cause message
                    else:
                        colored_lines.append(f"{current_indent}{current_line}")
                    i += 1

            # Check if this is a child log line (indented with spaces followed by [LEVEL])
            elif line.lstrip().startswith("["):
                # Extract the child log level
                parts = line.split("]", 1)
                if len(parts) > 1 and "[" in parts[0]:
                    child_level = parts[0].split("[")[1].lower()
                    # Apply selective coloring to the child log line
                    colored_child_line = self._color_child_log_line(line, child_level)
                    colored_lines.append(colored_child_line)
                else:
                    colored_lines.append(line)  # Keep as is if can't parse
                i += 1
            else:
                # Any other line, add as is
                colored_lines.append(line)
                i += 1

        # Join all lines back together
        return "\n".join(colored_lines)

    def _color_log_line(self, line: str, level: str) -> str:
        """Apply selective coloring to a single log line.

        Args:
            line: The log line to color.
            level: The log level.

        Returns:
            The colored log line.
        """
        # Split the log line into parts
        parts = line.split(" ", 2)  # Split into timestamp, [LEVEL], and the rest
        if len(parts) < 3:
            return line  # Return original line if it doesn't match expected format

        timestamp = parts[0]
        level_part = parts[1]
        rest = parts[2]

        # Pad the level inside the brackets for consistent width
        # Extract the level from [LEVEL]
        if level_part.startswith("[") and level_part.endswith("]"):
            level_text = level_part[1:-1]
            # Pad to 8 characters (length of "CRITICAL")
            padded_level = level_text.ljust(8)
            # Reconstruct with padding
            level_part = f"[{padded_level}]"

        # Apply colors to level based on log level
        level_color = self._get_level_color(level)

        # Check if there's an event (contains a colon)
        if ":" in rest:
            # Split into event and the rest
            event_rest = rest.split(":", 1)
            event = event_rest[0]
            rest_parts = event_rest[1].strip().split(" ", 1)
            message = rest_parts[0]
            context = rest_parts[1] if len(rest_parts) > 1 else ""

            # Reconstruct with event in white, message in gray
            colored_line = f"{timestamp} {level_color}{level_part}\033[0m {event}:\033[90m {message}\033[0m"
        else:
            # No event, just message and possibly context
            rest_parts = rest.split(" ", 1)
            message = rest_parts[0]
            context = rest_parts[1] if len(rest_parts) > 1 else ""

            # Reconstruct with message in gray
            colored_line = (
                f"{timestamp} {level_color}{level_part}\033[0m\033[90m {message}\033[0m"
            )

        # Add context with colored keys and gray values if present
        if context:
            # Replace each key=value with colored key and gray value
            colored_context = ""
            context_parts = context.split(" ")
            for part in context_parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    colored_context += (
                        f" {level_color}{key}\033[0m=\033[90m{value}\033[0m"
                    )
                else:
                    colored_context += f" \033[90m{part}\033[0m"

            colored_line += colored_context

        return colored_line

    def _color_child_log_line(self, line: str, level: str) -> str:
        """Apply selective coloring to a child log line.

        Args:
            line: The child log line to color.
            level: The log level.

        Returns:
            The colored child log line.
        """
        # Split the child log line into parts
        # Format is typically "  [LEVEL] EVENT: MESSAGE context"
        prefix_end = line.find("[")
        if prefix_end == -1:
            return line  # Return original line if it doesn't match expected format

        prefix = line[:prefix_end]  # Indentation spaces

        # Find the end of the level part
        level_end = line.find("]", prefix_end)
        if level_end == -1:
            return line  # Return original line if it doesn't match expected format

        # Extract the level text and pad it
        level_text = line[prefix_end + 1 : level_end]
        padded_level = level_text.ljust(8)

        # Reconstruct the level part with padding
        level_part = f"[{padded_level}]"

        # Split the rest to get message and context
        rest = line[level_end + 1 :].strip()

        # Apply colors to level based on log level
        level_color = self._get_level_color(level)

        # Check if there's a colon (separating event and message)
        if ":" in rest:
            event_message = rest.split(":", 1)
            event = event_message[0].strip()
            rest_parts = event_message[1].strip().split(" ", 1)
            message = rest_parts[0]
            context = rest_parts[1] if len(rest_parts) > 1 else ""

            # Reconstruct with event in white, message in gray
            colored_line = f"{prefix}{level_color}{level_part}\033[0m {event}:\033[90m {message}\033[0m"
        else:
            # If no colon, treat the whole rest as message
            message_context = rest.split(" ", 1)
            message = message_context[0]
            context = message_context[1] if len(message_context) > 1 else ""

            # Reconstruct with message in gray
            colored_line = (
                f"{prefix}{level_color}{level_part}\033[0m\033[90m {message}\033[0m"
            )

        # Add context with colored keys and gray values if present
        if context:
            # Replace each key=value with colored key and gray value
            colored_context = ""
            context_parts = context.split(" ")
            for part in context_parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    colored_context += (
                        f" {level_color}{key}\033[0m=\033[90m{value}\033[0m"
                    )
                else:
                    colored_context += f" \033[90m{part}\033[0m"

            colored_line += colored_context

        return colored_line

    def _get_level_color(self, level: str) -> str:
        """Get the ANSI color code for a log level.

        Args:
            level: The log level.

        Returns:
            The ANSI color code.
        """
        if level == "debug":
            return "\033[37m"  # White
        elif level == "info":
            return "\033[34m"  # Blue
        elif level == "warning":
            return "\033[33m"  # Yellow
        elif level == "error":
            return "\033[31m"  # Red
        elif level == "critical":
            return "\033[41;37m"  # White on Red background
        else:
            return ""  # No color


class FileHandler(Handler):
    """Handler that outputs logs to a file."""

    def __init__(
        self,
        file_path: str,
        level: Optional[LogLevel] = None,
        serialize: bool = True,
        rotation: Optional[FileRotation] = None,
    ) -> None:
        """Initialize a FileHandler.

        Args:
            file_path: Path to the log file.
            level: Log level for this handler. If None, uses the global level.
            serialize: Whether to serialize logs as JSON.
            rotation: Optional FileRotation object for log rotation.
        """
        super().__init__(level, serialize)
        self.file_path = Path(file_path)
        self.rotation = rotation

        # Create directory if it doesn't exist
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Open the file and keep it open
        self._file: Optional[IO] = None
        self._open_file()

    def _open_file(self) -> None:
        """Open the log file."""
        try:
            if self._file is not None:
                self._file.close()

            # Line buffering (buffering=1) ensures writes are flushed on newlines
            self._file = open(self.file_path, "a", encoding="utf-8", buffering=1)
        except Exception:
            # If we can't open the file, set _file to None
            self._file = None
            # We could log this error, but that might cause recursion
            # Instead, we'll silently fail and try again on next emit

    def emit(self, log_entry: Dict[str, Any]) -> None:
        """Emit a log entry to the file.

        Args:
            log_entry: The log entry to emit.
        """
        formatted = self.format(log_entry)

        # Use lock to prevent interleaved output from multiple threads
        with self._lock:
            # Check if we need to rotate the file
            if self.rotation and self.rotation.should_rotate(self.file_path):
                self._rotate_file()

            # Ensure we have a file handle
            if self._file is None:
                self._open_file()

            # Write to file
            try:
                if self._file is not None:
                    self._file.write(formatted + "\n")
                    self._file.flush()  # Ensure data is written to disk
                else:
                    # Fallback to one-time open if we couldn't maintain the file handle
                    with open(self.file_path, "a", encoding="utf-8") as f:
                        f.write(formatted + "\n")
            except Exception:
                # If writing fails, try reopening the file
                self._open_file()
                if self._file is not None:
                    try:
                        self._file.write(formatted + "\n")
                        self._file.flush()
                    except Exception:
                        # Last resort: fall back to one-time open
                        try:
                            with open(self.file_path, "a", encoding="utf-8") as f:
                                f.write(formatted + "\n")
                        except Exception:
                            pass  # Silently fail if all attempts fail

    def close(self) -> None:
        """Close the file handle."""
        with self._lock:
            if self._file is not None:
                try:
                    self._file.close()
                except Exception:
                    pass
                finally:
                    self._file = None

    def _rotate_file(self) -> None:
        """Rotate the log file."""
        if not self.file_path.exists() or self.rotation is None:
            return

        # Close the current file handle
        if self._file is not None:
            self._file.close()
            self._file = None

        # Get the base path and extension
        base_path = self.file_path.with_suffix("")
        suffix = self.file_path.suffix

        # Shift existing rotated files
        for i in range(self.rotation.keep - 1, 0, -1):
            old_path = f"{base_path}.{i}{suffix}"
            new_path = f"{base_path}.{i + 1}{suffix}"

            if os.path.exists(old_path):
                if os.path.exists(new_path):
                    os.remove(new_path)
                os.rename(old_path, new_path)

        # Rotate the current file
        rotated_path = f"{base_path}.1{suffix}"
        if os.path.exists(rotated_path):
            os.remove(rotated_path)
        os.rename(self.file_path, rotated_path)

        # Compress if needed
        if self.rotation.compression and os.path.exists(rotated_path):
            if self.rotation.compression == "zip":
                with zipfile.ZipFile(f"{rotated_path}.zip", "w") as zipf:
                    zipf.write(rotated_path, arcname=os.path.basename(rotated_path))
            elif self.rotation.compression == "gzip":
                # Gzip compression
                with open(rotated_path, "rb") as f_in:
                    with gzip.open(f"{rotated_path}.gz", "wb") as f_out:
                        f_out.write(f_in.read())

            os.remove(rotated_path)

        # Reopen the file
        self._open_file()

    def __del__(self) -> None:
        """Destructor to ensure file is closed when handler is garbage collected."""
        self.close()
