"""
ctxlog - A structured logging library for Python.

This library provides a structured logging system with context-rich logs,
multiple output handlers, and support for traditional log levels.
"""

from .config import _global_config, configure  # noqa: F401
from .handlers import ConsoleHandler, FileHandler, FileRotation, Handler
from .level import LevelSpec, LevelStr, LogLevel
from .log import Log
from .logger import Logger


def get_logger(name: str) -> Logger:
    """Get a logger for a module or class.

    Args:
        name: The name of the logger, typically __name__.

    Returns:
        A Logger instance.

    Example:
        ```python
        logger = ctxlog.get_logger(__name__)
        ```
    """
    return Logger(name)


__all__ = [
    "LogLevel",
    "Handler",
    "ConsoleHandler",
    "FileHandler",
    "FileRotation",
    "Log",
    "Logger",
    "LevelSpec",
    "LevelStr",
    "configure",
    "get_logger",
]
