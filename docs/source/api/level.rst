Log Levels
==========

This module provides log level definitions for ctxlog.

.. automodule:: ctxlog.level
   :members:
   :undoc-members:
   :show-inheritance:

LogLevel Enum
-------------

.. autoclass:: ctxlog.level.LogLevel
   :members:
   :undoc-members:
   :show-inheritance:

Type Aliases
------------

.. autodata:: ctxlog.level.LevelStr
   :annotation: = Literal["debug", "info", "warning", "error", "critical"]

.. autodata:: ctxlog.level.LevelSpec
   :annotation: = Union[LogLevel, LevelStr, int]
