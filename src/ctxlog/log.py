import datetime
import traceback
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

from .level import LogLevel

T = TypeVar("T", bound="Log")


class Log:
    """A log context with methods for adding structured fields and emitting logs."""

    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        event: Optional[str] = None,
        parent: Optional["Log"] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a Log context.

        Args:
            level: The log level.
            event: The event name.
            parent: The parent log context, if this is a chained log.
            **kwargs: Additional context fields.
        """
        self.level = level
        self.event = event
        self.parent = parent
        self.context: Dict[str, Any] = kwargs.copy()
        self.debug_context: Dict[str, Any] = {}
        self.error_context: Dict[str, Any] = {}
        self.exception_info: Optional[Dict[str, Any]] = None
        self.children: List["Log"] = []
        self.message: Optional[str] = None
        self.start_time = datetime.datetime.now().isoformat()

        # If this is a chained log, add it to the parent's children
        if parent is not None:
            parent.children.append(self)

    def ctx(self, level: LogLevel = LogLevel.INFO, **kwargs: Any) -> "Log":
        """Add context fields to the log.

        Args:
            level: The log level for these context fields.
            **kwargs: Context fields to add.

        Returns:
            Self for method chaining.
        """
        self.context.update(kwargs)
        return self

    def debug_ctx(self, **kwargs: Any) -> "Log":
        """Add debug-level context fields to the log.

        These fields will only be included in the output if debug logging is enabled.

        Args:
            **kwargs: Debug context fields to add.

        Returns:
            Self for method chaining.
        """
        self.debug_context.update(kwargs)
        return self

    def error_ctx(self, **kwargs: Any) -> "Log":
        """Add error-level context fields to the log.

        These fields will only be included in the output if the log level is error or higher.

        Args:
            **kwargs: Error context fields to add.

        Returns:
            Self for method chaining.
        """
        self.error_context.update(kwargs)
        return self

    def exc(self, exception: Exception) -> "Log":
        """Attach exception details to the log.

        Args:
            exception: The exception to attach.

        Returns:
            Self for method chaining.
        """
        self.exception_info = {
            "type": exception.__class__.__name__,
            "value": str(exception),
            "traceback": "".join(traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )),
        }
        return self

    def new(self, event: Optional[str] = None, **kwargs: Any) -> "Log":
        """Create a new log context chained to this one.

        Args:
            event: The event name for the new log.
            **kwargs: Context fields for the new log.

        Returns:
            A new Log instance chained to this one.
        """
        return Log(level=self.level, event=event, parent=self, **kwargs)

    def _build_log_entry(self, include_debug: bool = False) -> Dict[str, Any]:
        """Build a log entry dictionary.

        Args:
            include_debug: Whether to include debug context fields.

        Returns:
            A dictionary representing the log entry.
        """
        # Start with basic fields
        entry: Dict[str, Any] = {
            "level": str(self.level),
            "start_time": self.start_time,
        }

        # Add event if present
        if self.event:
            entry["event"] = self.event

        # Add message if present
        if self.message:
            entry["message"] = self.message

        # Add context fields
        entry.update(self.context)

        # Add debug context if requested
        if include_debug:
            entry.update(self.debug_context)

        # Add error context if this is an error or higher
        if self.level.value >= LogLevel.ERROR.value:
            entry.update(self.error_context)

        # Add exception info if present
        if self.exception_info:
            entry["exception"] = self.exception_info

        # Add children if present
        if self.children:
            entry["children"] = [
                child._build_log_entry(include_debug=include_debug)
                for child in self.children
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
        if self.parent is not None:
            return

        # Otherwise, build the log entry and emit it
        from . import _global_config

        # Add timestamp
        entry = self._build_log_entry(include_debug=_global_config.debug)
        entry["timestamp"] = datetime.datetime.now().isoformat()

        # Emit to all handlers
        for handler in _global_config.handlers:
            # Skip if the handler has a level and this log is below it
            if handler.level is not None and level.value < handler.level.value:
                continue

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