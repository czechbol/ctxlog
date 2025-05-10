Advanced Usage
==============

Contextual Logging
------------------

One of the key features of ctxlog is the ability to add context to your logs. This is particularly useful for tracking complex operations across multiple functions or modules.

.. code-block:: python

    def process_payment(payment):
        log = logger.new(event="payment_process").ctx(payment_id=payment.id)
        try:
            transaction_id = charge_payment(payment)
            log.ctx(transaction_id=transaction_id).info("Payment processed")
        except Exception as e:
            log.exc(e).error("Payment failed")

Log Chaining
------------

Log chaining allows you to create a hierarchy of logs for complex operations. This is useful for tracking multi-step processes and maintaining context across different stages.

.. code-block:: python

    def process_order(order):
        log = logger.new(event="order_process").ctx(order_id=order.id)
        validate_order(log.new("validation"), order)
        log.info("Order processed")

    def validate_order(log, order):
        log = log.ctx(order_id=order.id)

        # Perform validation

        log.info("Order validated")

When the parent log is emitted, all child logs are included in the output. This creates a structured log entry that shows the entire process flow.

Exception Handling
------------------

ctxlog provides a convenient way to attach exception details to logs:

.. code-block:: python

    try:
        # Some code that might raise an exception
        result = 1 / 0
    except Exception as e:
        log = logger.new()
        log.exc(e).error("Operation failed")

The ``exc()`` method attaches the exception type, message, and traceback to the log entry. This makes it easier to debug issues in production.

Thread Safety
-------------

ctxlog is designed to be thread-safe. Each handler uses a lock to prevent interleaved output from multiple threads.

Custom Handlers
---------------

You can create custom handlers by extending the ``Handler`` base class:

.. code-block:: python

    from ctxlog import Handler, LogLevel

    class CustomHandler(Handler):
        def __init__(self, level=None, serialize=False):
            super().__init__(level, serialize)
            # Initialize your handler

        def emit(self, log_entry):
            # Implement your custom emission logic
            formatted = self.format(log_entry)
            # Send the formatted log to your destination

        def close(self):
            # Clean up any resources
            pass

Performance Considerations
--------------------------

For high-performance applications, consider the following:

1. **Lazy Evaluation**: Use the ``new()`` method to create a log context, but only call the logging methods (``info()``, ``error()``, etc.) if the log will actually be emitted:

   .. code-block:: python

       log = logger.new()
       log.ctx(user_id=user.id)

       # Only build and emit the log if needed
       if expensive_condition():
           log.info("Expensive operation completed")

2. **Handler Levels**: Set appropriate levels for each handler to minimize processing:

   .. code-block:: python

       # Console gets INFO and above
       console_handler = ConsoleHandler(level=LogLevel.INFO)

       # File gets everything for debugging
       file_handler = FileHandler(
           level=LogLevel.DEBUG,
           file_path="debug.log"
       )

3. **Serialization**: Only use ``serialize=True`` when needed, as JSON serialization adds overhead.

Integration with Other Libraries
--------------------------------

ctxlog can be integrated with other logging systems:

.. code-block:: python

    import logging
    from ctxlog import Handler

    class PythonLoggingHandler(Handler):
        def __init__(self, logger_name="ctxlog", level=None, serialize=False):
            super().__init__(level, serialize)
            self.logger = logging.getLogger(logger_name)

        def emit(self, log_entry):
            level_name = log_entry.get("level", "").upper()
            message = self.format(log_entry)

            # Map ctxlog levels to Python logging levels
            if level_name == "DEBUG":
                self.logger.debug(message)
            elif level_name == "INFO":
                self.logger.info(message)
            elif level_name == "WARNING":
                self.logger.warning(message)
            elif level_name == "ERROR":
                self.logger.error(message)
            elif level_name == "CRITICAL":
                self.logger.critical(message)
