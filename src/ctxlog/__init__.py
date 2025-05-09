"""
ctxlog - A structured logging library for Python.

This library provides a structured logging system with context-rich logs,
multiple output handlers, and support for traditional log levels.
"""

import datetime
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .handlers import ConsoleHandler, FileHandler, FileRotation, Handler
from .level import LogLevel, LevelSpec, LevelStr
from .log import Log
from .logger import Logger


@dataclass
class _GlobalConfig:
    """Global configuration for ctxlog."""

    level: LogLevel = LogLevel.INFO
    debug: bool = False
    timefmt: str = "iso"
    handlers: List[Handler] = field(default_factory=list)


# Global configuration instance
_global_config = _GlobalConfig()


def configure(
    level: LevelSpec = LogLevel.INFO,
    debug: bool = False,
    timefmt: str = "iso",
    handlers: Optional[List[Handler]] = None,
) -> None:
    """Configure the global settings for ctxlog.

    This function should be called once, typically at application startup.

    Args:
        level: The global log level. Can be a LogLevel enum value, a string, or an int.
        debug: Whether to enable debug logging globally.
        timefmt: Timestamp format for log entries. Use 'iso' for ISO8601, or provide a custom strftime format string.
        handlers: List of output handlers. If None, a default ConsoleHandler will be used.

    Example:
        ```python
        ctxlog.configure(
            level=ctxlog.LogLevel.INFO,
            timefmt="iso",
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
    if isinstance(level, str):
        _global_config.level = LogLevel.from_string(level)
    elif isinstance(level, int):
        # Find the closest log level
        for log_level in LogLevel:
            if log_level.value == level:
                _global_config.level = log_level
                break
        else:
            # If no exact match, use the closest level
            if level < LogLevel.DEBUG.value:
                _global_config.level = LogLevel.DEBUG
            elif level > LogLevel.CRITICAL.value:
                _global_config.level = LogLevel.CRITICAL
            else:
                # Find the closest level
                closest_level = LogLevel.DEBUG
                closest_diff = abs(level - LogLevel.DEBUG.value)

                for log_level in LogLevel:
                    diff = abs(level - log_level.value)
                    if diff < closest_diff:
                        closest_level = log_level
                        closest_diff = diff

                _global_config.level = closest_level
    else:
        _global_config.level = level

    _global_config.debug = debug
    _global_config.timefmt = timefmt

    # Set up handlers
    if handlers is None:
        _global_config.handlers = [ConsoleHandler()]
    else:
        _global_config.handlers = handlers


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


# Initialize with default configuration if not already configured
if not _global_config.handlers:
    configure()


__all__ = [
    "LogLevel",
    "Handler",
    "ConsoleHandler",
    "FileHandler",
    "FileRotation",
    "Log",
    "Logger",
    "configure",
    "get_logger",
]