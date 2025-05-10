# ctxlog - Structured Logging Library for Python

`ctxlog` is a structured logging library for Python, designed for clarity, flexibility, and context-rich logs. It supports multiple output handlers, structured context, exception logging, and traditional log levels (`debug`, `info`, `warning`, `error`, `critical`), with optional JSON serialization.

## Features

- **Structured, context-rich logging**: Add structured fields to your logs for better filtering and analysis
- **Multiple output handlers**: Console and file output with customizable formatting
- **Log levels**: Traditional log levels (`debug`, `info`, `warning`, `error`, `critical`)
- **Exception logging**: Attach exception details to your logs
- **Context chaining**: Create child logs that inherit context from parent logs
- **File rotation**: Rotate log files based on size or time
- **Colored console output**: Make your logs more readable in the terminal
- **JSON serialization**: Output logs as JSON for easy parsing

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

# Configure ctxlog (optional, defaults to console output)
ctxlog.configure(
    level=ctxlog.LogLevel.INFO,
    handlers=[
        ctxlog.ConsoleHandler(serialize=False, color=True)
    ]
)

# Get a logger
logger = ctxlog.get_logger(__name__)

# Simple logging
logger.info("Hello, world!")

# Structured logging
logger.new().ctx(user_id="123", action="login").info("User logged in")

# Exception logging
try:
    # Some code that might raise an exception
    raise ValueError("Something went wrong")
except Exception as e:
    logger.new().exc(e).error("Operation failed")
```

## Configuration

Global configuration is performed via `ctxlog.configure()` and should be called once, typically at application startup.

```python
ctxlog.configure(
    level=ctxlog.LogLevel.INFO,
    timefmt="iso",  # ISO8601 timestamp format
    utc=False,      # Use local time (set to True for UTC)
    handlers=[
        ctxlog.ConsoleHandler(serialize=False, color=True, use_stderr=False),
        ctxlog.FileHandler(
            level=ctxlog.LogLevel.DEBUG,
            serialize=True,
            file_path="./app.log",
            rotation=ctxlog.FileRotation(
                size="20MB",
                time="00.00",
                keep=5,
                compression="gzip"
            ),
        ),
    ]
)
```

## Usage Examples

### Simple Structured Logging

```python
def start_app():
    try:
        app.start()
    except Exception as e:
        logger.new().exc(e).error("Failed to start app")
```

### Contextual Structured Logging

```python
def process_payment(payment: Payment):
    log = logger.new()
    log.event = "new_payment"
    log.ctx(
        payment_id=payment.id,
        amount=payment.amount,
        currency=payment.currency
    )
    log.ctx(level=LogLevel.ERROR, customer_id=payment.customer.id)
    log.ctx(
        level=LogLevel.DEBUG,
        payment_method=payment.method,
        payment_gateway=payment.gateway.name,
    )

    try:
        validate_payment(payment)
        # ... business logic ...
        log.ctx(transaction_id="txn_456")
        log.info("Payment processed successfully")
    except ValidationError as e:
        log.exc(e).error("Validation failed")
    except PaymentProcessError as e:
        log.ctx(level=LogLevel.ERROR, error_code=e.code).exc(e).error("Payment failed")
```

### Log Chaining

```python
def process_order(order):
    log = logger.new()
    log.event = "new_order"
    log.ctx(order_id=order.id)
    log.ctx(level=LogLevel.ERROR, customer_id=order.customer.id)
    log.ctx(
        level=LogLevel.DEBUG,
        order_items=[item.id for item in order.items],
        order_total=order.total,
    )

    # Create a child log for validation
    validation_log = log.new(event="order_validation")

    try:
        validate_order(validation_log, order)
        # ... business logic ...
        log.info("Order processed successfully")
    except ValidationError as e:
        log.exc(e).error("Validation failed")
    except OrderProcessError as e:
        log.ctx(level=LogLevel.ERROR, error_code=e.code).exc(e).error("Order processing failed")
```

## Log Output Format

All logs are output as structured objects (dicts), optionally serialized as JSON.

### Example Outputs

**Info:**

```json
{
  "timestamp": "2023-10-01T12:00:00Z",
  "level": "info",
  "event": "new_payment",
  "message": "Payment processed successfully",
  "ctx_start": "2023-10-01T12:00:00Z",
  "payment_id": "pay_123",
  "amount": 100.0,
  "currency": "USD",
  "transaction_id": "txn_456"
}
```

**Error:**

```json
{
  "timestamp": "2023-10-01T12:00:00Z",
  "level": "error",
  "event": "new_payment",
  "message": "Payment failed",
  "ctx_start": "2023-10-01T12:00:00Z",
  "payment_id": "pay_123",
  "amount": 100.0,
  "currency": "USD",
  "customer_id": "cust_789",
  "error_code": "INVALID_CARD",
  "exception": {
    "type": "PaymentProcessError",
    "value": "Card expired",
    "traceback": "Traceback (most recent call last):\n  ..."
  }
}
```

## License

MIT
