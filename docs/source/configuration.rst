Configuration
=============

Global Configuration
--------------------

ctxlog uses a global configuration that can be customized using the ``configure`` function:

.. code-block:: python

    import ctxlog
    from ctxlog import LogLevel, ConsoleHandler, FileHandler, FileRotation

    # Configure with default console handler
    ctxlog.configure(
        level=LogLevel.INFO,
        timefmt="iso",  # or "%Y-%m-%d %H:%M:%S"
        utc=True,
    )

    # Configure with custom handlers
    ctxlog.configure(
        level=LogLevel.INFO,
        handlers=[
            ConsoleHandler(
                level=LogLevel.INFO,
                serialize=False,  # Human-readable format
                color=True,
                use_stderr=False,
            ),
            FileHandler(
                level=LogLevel.DEBUG,  # More verbose in file
                serialize=True,  # JSON format
                file_path="./app.log",
                rotation=FileRotation(
                    size="20MB",  # Rotate when file reaches 20MB
                    keep=5,  # Keep 5 rotated files
                    compression="gzip",  # Compress old files
                ),
            ),
        ],
    )

Configuration Parameters
------------------------

level
~~~~~

The global log level threshold. Logs below this level will not be emitted.

.. code-block:: python

    # Using enum
    level=ctxlog.LogLevel.INFO

    # Using string
    level="info"

    # Using integer
    level=20

Available log levels:

- ``DEBUG`` (10)
- ``INFO`` (20)
- ``WARNING`` (30)
- ``ERROR`` (40)
- ``CRITICAL`` (50)

timefmt
~~~~~~~

The timestamp format for log entries:

.. code-block:: python

    # ISO8601 format (default)
    timefmt="iso"

    # Custom strftime format
    timefmt="%Y-%m-%d %H:%M:%S"

utc
~~~

Whether to use UTC for timestamps:

.. code-block:: python

    # Use UTC (default: False)
    utc=True

    # Use local time
    utc=False

handlers
~~~~~~~~

A list of output handlers. If not provided, a default ``ConsoleHandler`` is used:

.. code-block:: python

    from ctxlog import ConsoleHandler, FileHandler

    handlers=[
        ConsoleHandler(),
        FileHandler(file_path="./app.log"),
    ]

Console Handler
---------------

The ``ConsoleHandler`` outputs logs to the console (stdout/stderr):

.. code-block:: python

    from ctxlog import ConsoleHandler, LogLevel

    ConsoleHandler(
        level=LogLevel.INFO,  # Handler-specific level (optional)
        serialize=False,      # Whether to output as JSON
        color=True,           # Whether to use colored output
        use_stderr=False,     # Whether to use stderr for all logs
    )

File Handler
------------

The ``FileHandler`` outputs logs to a file:

.. code-block:: python

    from ctxlog import FileHandler, FileRotation, LogLevel

    FileHandler(
        level=LogLevel.DEBUG,  # Handler-specific level (optional)
        serialize=True,        # Whether to output as JSON
        file_path="./app.log", # Path to the log file
        rotation=None,         # File rotation configuration (optional)
    )

File Rotation
-------------

The ``FileRotation`` class configures log file rotation:

.. code-block:: python

    from ctxlog import FileRotation

    # Size-based rotation
    rotation=FileRotation(
        size="20MB",        # Rotate when file reaches this size
        keep=5,             # Keep this many rotated files
        compression="gzip", # Compress old files (gzip or zip)
    )

    # Time-based rotation
    rotation=FileRotation(
        time="00.00",       # Rotate at this time (HH.MM)
        keep=5,             # Keep this many rotated files
        compression="gzip", # Compress old files (gzip or zip)
    )

Multiple Handlers
-----------------

You can configure multiple handlers with different levels and formats:

.. code-block:: python

    import ctxlog
    from ctxlog import ConsoleHandler, FileHandler, FileRotation, LogLevel

    ctxlog.configure(
        level=LogLevel.INFO,
        handlers=[
            ConsoleHandler(
                level=LogLevel.INFO,
                serialize=False,  # Human-readable format
                color=True,
                use_stderr=False,
            ),
            FileHandler(
                level=LogLevel.DEBUG,  # More verbose in file
                serialize=True,  # JSON format
                file_path="./app.log",
                rotation=FileRotation(
                    size="20MB",  # Rotate when file reaches 20MB
                    keep=5,  # Keep 5 rotated files
                    compression="gzip",  # Compress old files
                ),
            ),
        ],
    )
