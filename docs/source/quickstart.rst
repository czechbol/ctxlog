Quick Start
===========

Basic Usage
----------

Here's a simple example to get you started with ctxlog:

.. code-block:: python

    import ctxlog

    # Configure the logger (optional, uses sensible defaults)
    ctxlog.configure(
        level="debug",  # or ctxlog.LogLevel.INFO
        timefmt="iso",  # ISO8601 format
        utc=True,  # Use UTC for timestamps
    )

    # Simple logging
    logger.debug("This is a simple debug log")
    logger.info("This is a simple info log")
    logger.warning("This is a simple warning log")
    logger.error("This is a simple error log")
    logger.critical("This is a simple critical log")

    # Structured logging with context
    log = logger.ctx(user_id="user123", action="login").info("User logged in")

    # Exception handling
    try:
        # Some code that might raise an exception
        result = 1 / 0
    except Exception as e:
        log = logger.ctx(dividing=1, by=0)
        log.exc(e).error("Division failed")

Log Chaining
-----------

For complex operations, you can create a hierarchy of logs:

.. code-block:: python

    def process_data(data):
        log = logger.new("data_processing")

        try:
            validate_data(log.new("data_validation"), data)
        except Exception as e:
            log.exc(e).error("Data validation failed")

        log.info("Data processed successfully")

    def validate_data(log, data):
        log = log.ctx(key=data["key"])

        # Validation happens

        log.info("Data validation successful")

    process_data({"key": "value"})

Output Handlers
-------------

ctxlog supports multiple output handlers:

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
