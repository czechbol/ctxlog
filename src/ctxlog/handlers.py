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

            return file_path.stat().st_size >= max_bytes

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
            return json.dumps(log_entry)

        # Human-readable format
        timestamp = log_entry.get("timestamp", "")
        level = log_entry.get("level", "").upper()
        event = log_entry.get("event", "")
        message = log_entry.get("message", "")

        # Format basic log line
        log_line = f"{timestamp} [{level}] {event}: {message}"

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
                "start_time",
            ]:
                context_fields.append(f"{key}={value}")

        if context_fields:
            log_line += " " + " ".join(context_fields)

        # Add exception if present
        if "exception" in log_entry:
            exc = log_entry["exception"]
            log_line += f"\nException: {exc.get('type')}: {exc.get('value')}"
            if "traceback" in exc:
                log_line += f"\n{exc['traceback']}"

        # Add children if present
        if "children" in log_entry and log_entry["children"]:
            log_line += "\nChild logs:"
            for i, child in enumerate(log_entry["children"], 1):
                child_level = child.get("level", "").upper()
                child_event = child.get("event", "")
                child_message = child.get("message", "")
                log_line += f"\n  {i}. [{child_level}] {child_event}: {child_message}"

        return log_line


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
        formatted = self.format(log_entry)

        if self.color and not self.serialize:
            # Add ANSI color codes based on log level
            level = log_entry.get("level", "").lower()
            if level == "debug":
                formatted = f"\033[36m{formatted}\033[0m"  # Cyan
            elif level == "info":
                formatted = f"\033[32m{formatted}\033[0m"  # Green
            elif level == "warning":
                formatted = f"\033[33m{formatted}\033[0m"  # Yellow
            elif level == "error":
                formatted = f"\033[31m{formatted}\033[0m"  # Red
            elif level == "critical":
                formatted = f"\033[31;1m{formatted}\033[0m"  # Bold Red

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
