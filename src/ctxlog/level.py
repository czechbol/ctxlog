from enum import Enum, auto
from typing import Literal, Union


class LogLevel(Enum):
    """Log levels for ctxlog."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @classmethod
    def from_string(cls, level_str: str) -> "LogLevel":
        """Convert a string to a LogLevel.

        Args:
            level_str: The string representation of the log level.

        Returns:
            The corresponding LogLevel enum value.

        Raises:
            ValueError: If the string is not a valid log level.
        """
        level_map = {
            "debug": cls.DEBUG,
            "info": cls.INFO,
            "warning": cls.WARNING,
            "error": cls.ERROR,
            "critical": cls.CRITICAL,
        }

        if level_str.lower() not in level_map:
            valid_levels = ", ".join(level_map.keys())
            raise ValueError(f"Invalid log level: {level_str}. Valid levels are: {valid_levels}")

        return level_map[level_str.lower()]

    def __str__(self) -> str:
        """Return the string representation of the log level."""
        return self.name.lower()


# Type aliases
LevelStr = Literal["debug", "info", "warning", "error", "critical"]
LevelSpec = Union[LogLevel, LevelStr, int]