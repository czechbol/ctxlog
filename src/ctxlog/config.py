"""
Global configuration for ctxlog.

This module contains the global configuration class and instance used by the logging system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .handlers import ConsoleHandler, Handler
from .level import LevelSpec, LogLevel


@dataclass
class _GlobalConfig:
    """Global configuration for ctxlog."""

    level: LogLevel = LogLevel.INFO
    timefmt: str = "iso"
    utc: bool = False
    handlers: List[Handler] = field(default_factory=list)


# Global configuration instance
_global_config = _GlobalConfig()


def configure(
    level: LevelSpec = LogLevel.INFO,
    timefmt: str = "iso",
    utc: bool = False,
    handlers: Optional[List[Handler]] = None,
) -> None:
    """Configure the global settings for ctxlog.

    This function should be called once, typically at application startup.

    Args:
        level: The global log level. Can be a LogLevel enum value, a string, or an int.
        timefmt: Timestamp format for log entries. Use 'iso' for ISO8601, or provide a custom strftime format string.
        utc: If True, use UTC for timestamps. Default is False (local time).
        handlers: List of output handlers. If None, a default ConsoleHandler will be used.

    Example:
        ```python
        ctxlog.configure(
            level=ctxlog.LogLevel.INFO,
            timefmt="iso",
            utx=True,
            handlers=[
                ctxlog.ConsoleHandler(serialize=False, color=True, use_stderr=False),
                ctxlog.FileHandler(
                    level=ctxlog.LogLevel.DEBUG,
                    serialize=True,
                    file_path="./app.log",
                    rotation=ctxlog.FileRotation(
                        size="20MB",
                        time="00.00",
                        keep=12,
                        compress_old=True
                    ),
                ),
            ]
        )
        ```
    """
    global _global_config

    # Convert level to LogLevel if it's a string or int
    try:
        _global_config.level = LogLevel.parse(level)
    except ValueError:
        raise ValueError(
            f"Invalid log level: {level}. Use a LogLevel enum, a string, or an int."
        )

    if timefmt != "iso" and not isinstance(timefmt, str):
        raise TypeError("timefmt must be a string or 'iso'.")
    else:
        try:
            datetime.now().strftime(timefmt)
        except ValueError:
            raise ValueError(
                f"Invalid timefmt: {timefmt}. Use 'iso' or a valid strftime format string."
            )

    _global_config.timefmt = timefmt
    _global_config.utc = utc

    # Set up handlers
    if handlers is None:
        _global_config.handlers = [ConsoleHandler()]
    else:
        _global_config.handlers = handlers


# Initialize with default configuration if not already configured
if not _global_config.handlers:
    configure()
