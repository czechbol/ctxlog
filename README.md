# ctxlog

[![PyPI version](https://img.shields.io/pypi/v/ctxlog.svg)](https://pypi.org/project/ctxlog/)
[![Python versions](https://img.shields.io/pypi/pyversions/ctxlog.svg)](https://pypi.org/project/ctxlog/)
[![License](https://img.shields.io/pypi/l/ctxlog.svg)](https://github.com/czechbol/ctxlog/blob/main/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/ctxlog/badge/?version=latest)](https://ctxlog.readthedocs.io/en/latest/?badge=latest)

A structured logging library for Python that provides nested, context-rich logs.

This library was inspired by the [Canonical Log Lines](https://brandur.org/canonical-log-lines), which emphasizes the importance of reducing the amount of noise in logs for better observability and debugging. With the addition of log chaining, `ctxlog` allows to create log trees that can be used to track complex operations and their context, similar to tracing mechanisms.

## Features

- **Structured Logging**: Structured logs with context fields with optional JSON serialization
- **Context-Rich**: Extend the logs with additional context information over the course of an action
- **Log Chaining**: Create nested log contexts for tracking complex operations

## Documentation

Full documentation is available at [ctxlog.readthedocs.io](https://ctxlog.readthedocs.io/).

## Installation

```bash
pip install ctxlog
```

Or with Poetry:

```bash
poetry add ctxlog
```

## Quick Start

```python
import ctxlog

# Configure the logger (optional, uses sensible defaults)
ctxlog.configure(
    level="debug",  # or ctxlog.LogLevel.INFO
    timefmt="iso",  # ISO8601 format
    utc=True,  # Use UTC for timestamps
)

# Create a logger instance
logger = ctxlog.get_logger("example")

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
    log = logger.new("exception_example").ctx(dividing=1, by=0)
    log.exc(e).error("Division failed")

# Log chaining for complex operations
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
```

#### Produces the following output

<p align="center">
  <img src="docs/source/_static/quickstart.png" alt="quickstart example output">
</p>

## Configuration

### Global Configuration

```python
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
```

### Log Levels

ctxlog supports the standard log levels:

- `DEBUG` (10)
- `INFO` (20)
- `WARNING` (30)
- `ERROR` (40)
- `CRITICAL` (50)

## Advanced Usage

### Contextual Logging

```python
def process_payment(payment):
    log = logger.new(event="payment_process").ctx(payment_id=payment.id)
    try:
        transaction_id = charge_payment(payment)
        log.ctx(transaction_id=transaction_id).info("Payment processed")
    except Exception as e:
        log.exc(e).error("Payment failed")
```

### Log Chaining

```python
def process_order(order):
    log = logger.new(event="order_process").ctx(order_id=order.id)
    validate_order(log.new("validation"), order)
    log.info("Order processed")

def validate_order(log, order):
    log = log.ctx(order_id=order.id)

    # Perform validation

    log.info("Order validated")
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Documentation

The documentation is built using Sphinx and hosted on ReadTheDocs. To build the documentation locally:

```bash
# Install development dependencies with documentation extras
poetry install --with docs

# Build the documentation
cd docs
poetry run make html
cd ..
```

The built documentation will be available in the `docs/build/html` directory.
