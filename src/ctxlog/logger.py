from typing import Any, Dict, Optional, Type, TypeVar

from .level import LogLevel
from .log import Log

T = TypeVar("T", bound="Logger")


class Logger:
    """Main entry point for ctxlog.

    This class provides methods for creating log contexts and emitting logs.
    """

    def __init__(self, name: str) -> None:
        """Initialize a Logger.

        Args:
            name: The name of the logger, typically the module name.
        """
        self.name = name

    def new(self) -> Log:
        """Create a new log context without any extra fields.

        Returns:
            A new Log instance.
        """
        return Log(event=self.name)

    def ctx(self, level: LogLevel = LogLevel.INFO, **kwargs: Any) -> Log:
        """Create a new log context with structured fields.

        Args:
            level: The log level for these context fields.
            **kwargs: Context fields to add.

        Returns:
            A new Log instance with the specified context fields.
        """
        log = Log(level=level, event=kwargs.get("event", self.name))
        return log.ctx(**kwargs)

    def debug_ctx(self, **kwargs: Any) -> Log:
        """Create a new log context with debug-level structured fields.

        Args:
            **kwargs: Debug context fields to add.

        Returns:
            A new Log instance with the specified debug context fields.
        """
        log = Log(level=LogLevel.DEBUG, event=kwargs.get("event", self.name))
        return log.debug_ctx(**kwargs)

    def error_ctx(self, **kwargs: Any) -> Log:
        """Create a new log context with error-level structured fields.

        Args:
            **kwargs: Error context fields to add.

        Returns:
            A new Log instance with the specified error context fields.
        """
        log = Log(level=LogLevel.ERROR, event=kwargs.get("event", self.name))
        return log.error_ctx(**kwargs)

    def exc(self, exception: Exception) -> Log:
        """Create a new log context with exception details.

        Args:
            exception: The exception to attach.

        Returns:
            A new Log instance with the specified exception details.
        """
        log = Log(level=LogLevel.ERROR, event=self.name)
        return log.exc(exception)

    def debug(self, message: str) -> None:
        """Log a debug message.

        Args:
            message: The log message.
        """
        self.new().debug(message)

    def info(self, message: str) -> None:
        """Log an info message.

        Args:
            message: The log message.
        """
        self.new().info(message)

    def warning(self, message: str) -> None:
        """Log a warning message.

        Args:
            message: The log message.
        """
        self.new().warning(message)

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: The log message.
        """
        self.new().error(message)

    def critical(self, message: str) -> None:
        """Log a critical message.

        Args:
            message: The log message.
        """
        self.new().critical(message)