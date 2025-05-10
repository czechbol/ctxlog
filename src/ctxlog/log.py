import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .level import LogLevel


class LogContext:
    """A class to store context fields categorized by log level."""

    def __init__(self) -> None:
        """Initialize an empty LogContext."""
        from .config import _global_config

        self.config = _global_config
        self._contexts: Dict[LogLevel, Dict[str, Any]] = {
            level: {} for level in LogLevel
        }

    def add(self, level: LogLevel, **kwargs: Any) -> None:
        """Add context fields at the specified log level.

        Args:
            level: The log level for these context fields.
            **kwargs: Context fields to add.
        """
        for key, value in kwargs.items():
            if isinstance(value, datetime):
                # Convert datetime to string
                if self.config.utc and value.tzinfo is not None:
                    value = value.astimezone(timezone.utc)
                kwargs[key] = _format_date(value, self.config.timefmt)
        self._contexts[level].update(kwargs)

    def get_for_level(self, level: LogLevel) -> Dict[str, Any]:
        """Get all context fields that should be included for a given log level.

        Args:
            level: The log level to get context for.

        Returns:
            A dictionary of context fields.
        """
        result: Dict[str, Any] = {}

        # Include context from all levels up to and including the specified level
        for ctx_level in LogLevel:
            if ctx_level.value <= level.value:
                result.update(self._contexts[ctx_level])

        return result


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
            self.start_time = _format_date(
                datetime.now(timezone.utc), self.config.timefmt
            )
        else:
            self.start_time = _format_date(datetime.now(), self.config.timefmt)
        self.message: Optional[str] = None
        self._context = LogContext()
        self.exception_info: Optional[Dict[str, Any]] = None
        self.children: List["Log"] = []

    def ctx(self, level: LogLevel = LogLevel.INFO, **kwargs: Any) -> "Log":
        """Add context fields to the log at the specified level.

        Args:
            level: The log level for these context fields.
            **kwargs: Context fields to add.

        Returns:
            Self for method chaining.
        """
        self._context.add(level, **kwargs)
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
        else:
            # If no traceback is available, create a simple one
            self.exception_info["traceback"] = (
                f"Traceback (most recent call last):\n{exception.__class__.__name__}: {str(exception)}\n"
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
            "start_time": self.start_time,
        }

        level = self.level if self.level else LogLevel.INFO

        # Add event if present
        if self.event:
            entry["event"] = self.event

        # Add message if present
        if self.message:
            entry["message"] = self.message

        # Add context fields appropriate for this log level
        entry.update(self._context.get_for_level(level=level))

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
