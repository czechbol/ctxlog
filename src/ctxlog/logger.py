from typing import Optional, Union

from .log import Log


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

    def new(self, event: Optional[str] = None) -> Log:
        """Create a new log context without any extra fields.

        Returns:
            A new Log instance.
        """
        return Log(event=event)

    def ctx(self, **kwargs: dict[str, Union[str, int, float, bool, None]]) -> Log:
        """Create a new log context with additional fields. Use `.new().ctx()` instead if you want to set an event name.

        Args:
            **kwargs: Additional fields to include in the log context.

        Returns:
            A new Log instance with the provided context.
        """
        return self.new().ctx(**kwargs)

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
