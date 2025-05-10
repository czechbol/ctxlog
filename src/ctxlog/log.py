import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from .level import LogLevel


class LogContext:
    """A class to store context fields."""

    def __init__(self) -> None:
        """Initialize an empty LogContext."""
        from .config import _global_config

        self.config = _global_config
        self._context: Dict[str, Any] = {}

    def _is_json_serializable_type(self, value: Any) -> bool:
        """Recursively check if value is a JSON-serializable type."""
        if value is None:
            return True
        if isinstance(value, (str, int, float, bool)):
            return True
        return False

    def add(self, **kwargs: dict[str, Union[str, int, float, bool, None]]) -> None:
        """Add context fields.

        Args:
            **kwargs: Context fields to add.
        """

        # Only allow JSON-serializable types (by type, not by dump)
        for k, v in kwargs.items():
            if not self._is_json_serializable_type(v):
                raise TypeError(
                    f"Context field '{k}' with value '{v}' is not a JSON-serializable type."
                )
        self._context.update(kwargs)

    def get_all(self) -> Dict[str, Any]:
        """Get all context fields.

        Returns:
            A dictionary of all context fields.
        """
        return self._context.copy()


class Log:
    """A log context with methods for adding structured fields and emitting logs."""

    def __init__(
        self,
        event: Optional[str] = None,
        has_parent: bool = False,
    ) -> None:
        """Initialize a Log context.

        Args:
            level: The log level.
            event: The event name.
            has_parent: Whether this log context has a parent.
            **kwargs: Additional context fields.
        """
        from .config import _global_config

        self.config = _global_config
        self.level: Optional[LogLevel] = None
        self.event = event
        self._has_parent = has_parent
        if self.config.utc:
            self.ctx_start = _format_date(
                datetime.now(timezone.utc), self.config.timefmt
            )
        else:
            self.ctx_start = _format_date(datetime.now(), self.config.timefmt)
        self.message: Optional[str] = None
        self._context = LogContext()
        self.exception_info: Optional[Dict[str, Any]] = None
        self.children: List["Log"] = []

    def ctx(self, **kwargs: dict[str, Union[str, int, float, bool, None]]) -> "Log":
        """Add context fields to the log.

        Args:
            **kwargs: Context fields to add.

        Returns:
            Self for method chaining.
        """
        self._context.add(**kwargs)
        return self

    def exc(self, exception: Exception) -> "Log":
        """Attach exception details to the log.

        Args:
            exception: The exception to attach.

        Returns:
            Self for method chaining.
        """
        # Create exception info dictionary
        self.exception_info = {
            "type": exception.__class__.__name__,
            "value": str(exception),
        }

        # Add traceback if available
        if exception.__traceback__ is not None:
            self.exception_info["traceback"] = "".join(
                traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
            )
        return self

    def new(self, event: Optional[str] = None, **kwargs: Any) -> "Log":
        """Create a new log context chained to this one.

        Args:
            event: The event name for the new log.
            **kwargs: Context fields for the new log.

        Returns:
            A new Log instance chained to this one.
        """
        child_log = Log(event=event, has_parent=True)
        self.children.append(child_log)
        return child_log

    def _build_log_entry(self, level: LogLevel) -> Dict[str, Any]:
        """Build a log entry dictionary.

        Args:
            level: The log level for the entry.

        Returns:
            A dictionary representing the log entry.
        """

        # Start with basic fields
        entry: Dict[str, Any] = {
            "level": str(self.level),
            "ctx_start": self.ctx_start,
        }

        level = self.level if self.level else LogLevel.INFO

        # Add event if present
        if self.event:
            entry["event"] = self.event

        # Add message if present
        if self.message:
            entry["message"] = self.message

        # Add all context fields
        entry.update(self._context.get_all())

        # Add exception info if present
        if self.exception_info:
            entry["exception"] = self.exception_info

        # Add children if present
        if self.children:
            entry["children"] = [
                child._build_log_entry(level=level) for child in self.children
            ]

        return entry

    def _emit(self, message: str, level: LogLevel) -> None:
        """Emit a log entry.

        This method is called by the debug(), info(), etc. methods.
        If this is a chained log, it sets the message and level but doesn't emit.

        Args:
            message: The log message.
            level: The log level.
        """
        self.message = message
        self.level = level

        # If this is a chained log, don't emit
        if self._has_parent:
            return

        # Emit to all handlers
        for handler in self.config.handlers:
            # get the handler level
            lvl = handler.level
            if lvl is None:
                lvl = self.config.level

            if self.level.value < lvl.value:
                # Skip if log level is lower than handler level
                # (e.g., skip DEBUG logs if handler level is INFO)
                continue

            entry = self._build_log_entry(level=lvl)

            # Add timestamp
            if self.config.utc:
                entry["timestamp"] = _format_date(
                    datetime.now(timezone.utc), self.config.timefmt
                )
            else:
                entry["timestamp"] = _format_date(datetime.now(), self.config.timefmt)

            handler.emit(entry)

    def debug(self, message: str) -> None:
        """Log a debug message.

        Args:
            message: The log message.
        """
        self._emit(message, LogLevel.DEBUG)

    def info(self, message: str) -> None:
        """Log an info message.

        Args:
            message: The log message.
        """
        self._emit(message, LogLevel.INFO)

    def warning(self, message: str) -> None:
        """Log a warning message.

        Args:
            message: The log message.
        """
        self._emit(message, LogLevel.WARNING)

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: The log message.
        """
        self._emit(message, LogLevel.ERROR)

    def critical(self, message: str) -> None:
        """Log a critical message.

        Args:
            message: The log message.
        """
        self._emit(message, LogLevel.CRITICAL)


def _format_date(date: datetime, timefmt: str) -> str:
    """Format a datetime object to a string based on the provided format.

    Args:
        date: The datetime object to format.
        timefmt: The format string. Use 'iso' for ISO8601, or provide a custom strftime format string.

    Returns:
        A formatted string representation of the date.
    """

    if timefmt == "iso":
        return date.isoformat()
    else:
        return date.strftime(timefmt)
