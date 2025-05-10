"""Integration tests for ctxlog."""

import io
import json
import os
import tempfile
from unittest.mock import patch

import pytest

import ctxlog
from ctxlog import LogLevel


class PaymentProcessError(Exception):
    """Example exception for testing."""

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


class ValidationError(Exception):
    """Example exception for testing."""

    pass


class Payment:
    """Example Payment class for testing."""

    def __init__(
        self, id, amount, currency, customer_id, method="credit_card", gateway="Stripe"
    ):
        self.id = id
        self.amount = amount
        self.currency = currency
        self.customer = Customer(customer_id)
        self.method = method
        self.gateway = Gateway(gateway)


class Customer:
    """Example Customer class for testing."""

    def __init__(self, id):
        self.id = id


class Gateway:
    """Example Gateway class for testing."""

    def __init__(self, name):
        self.name = name


def validate_payment(payment):
    """Example validation function."""
    if payment.amount <= 0:
        raise ValidationError("Payment amount must be positive")


# Helper class for testing
class MockHandler:
    """Mock handler for testing."""

    def __init__(self, level=None):
        self.logs = []
        self.level = level
        self.serialize = False

    def emit(self, log_entry):
        """Store the log entry."""
        self.logs.append(log_entry)


@pytest.fixture
def mock_stdout():
    """Fixture to capture stdout."""
    buffer = io.StringIO()
    with patch("sys.stdout", buffer):
        yield buffer
        buffer.seek(0)  # Reset buffer position for reading


def test_simple_structured_logging(mock_stdout):
    """Test simple structured logging example from the spec."""
    # Create a mock handler to capture the logs
    mock_handler = MockHandler()

    # Configure ctxlog with our mock handler
    ctxlog.configure(level=LogLevel.INFO, handlers=[mock_handler])

    logger = ctxlog.get_logger("test_module")

    # Test successful case
    try:
        # Simulate app.start()
        pass
    except Exception as e:
        log = logger.new()
        log.exc(e)
        log.error("Failed to start app")

    # Test error case
    try:
        # Simulate app.start() with error
        raise RuntimeError("App failed to start")
    except Exception as e:
        log = logger.new()
        log.exc(e)
        log.error("Failed to start app")

    # Check that we have one log entry (the error)
    assert len(mock_handler.logs) == 1

    # Check the log entry
    log_data = mock_handler.logs[0]
    assert log_data["level"] == "error"
    assert log_data["message"] == "Failed to start app"
    assert log_data["exception"]["type"] == "RuntimeError"
    assert log_data["exception"]["value"] == "App failed to start"


def test_contextual_structured_logging(mock_stdout):
    """Test contextual structured logging example from the spec."""
    # Create a mock handler to capture the logs
    mock_handler = MockHandler()

    # Configure ctxlog with our mock handler
    ctxlog.configure(
        level=LogLevel.DEBUG,  # Use DEBUG level instead of debug flag
        handlers=[mock_handler],
    )

    logger = ctxlog.get_logger("payment_processor")

    # Create a payment
    payment = Payment(
        id="pay_123",
        amount=100.0,
        currency="USD",
        customer_id="cust_789",
        method="credit_card",
        gateway="Stripe",
    )

    # Test successful payment processing
    def process_payment_success(payment):
        log = logger.new()
        log.event = "new_payment"
        log.ctx(
            payment_id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
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
            log.ctx(level=LogLevel.ERROR, error_code=e.code).exc(e).error(
                "Payment failed"
            )

    process_payment_success(payment)

    # Test failed payment processing
    def process_payment_failure(payment):
        log = logger.new()
        log.event = "new_payment"
        log.ctx(
            payment_id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
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
            raise PaymentProcessError("Card expired", "INVALID_CARD")
        except ValidationError as e:
            log.exc(e).error("Validation failed")
        except PaymentProcessError as e:
            log.ctx(level=LogLevel.ERROR, error_code=e.code).exc(e).error(
                "Payment failed"
            )

    process_payment_failure(payment)

    # Check that we have two log entries (success and failure)
    assert len(mock_handler.logs) == 2

    # Get the success and failure logs
    success_log = mock_handler.logs[0]
    failure_log = mock_handler.logs[1]

    # Check success log
    assert success_log["level"] == "info"
    assert success_log["event"] == "new_payment"
    assert success_log["message"] == "Payment processed successfully"
    assert success_log["payment_id"] == "pay_123"
    assert success_log["amount"] == 100.0
    assert success_log["currency"] == "USD"
    assert success_log["transaction_id"] == "txn_456"
    assert success_log["payment_method"] == "credit_card"  # Debug field included
    assert success_log["payment_gateway"] == "Stripe"  # Debug field included

    # Check failure log
    assert failure_log["level"] == "error"
    assert failure_log["event"] == "new_payment"
    assert failure_log["message"] == "Payment failed"
    assert failure_log["payment_id"] == "pay_123"
    assert failure_log["amount"] == 100.0
    assert failure_log["currency"] == "USD"
    assert failure_log["customer_id"] == "cust_789"  # Error field included
    assert failure_log["error_code"] == "INVALID_CARD"  # Error field included
    assert failure_log["payment_method"] == "credit_card"  # Debug field included
    assert failure_log["payment_gateway"] == "Stripe"  # Debug field included
    assert failure_log["exception"]["type"] == "PaymentProcessError"
    assert failure_log["exception"]["value"] == "Card expired"


def test_log_chaining(mock_stdout):
    """Test log chaining example from the spec."""
    # Create a mock handler to capture the logs
    mock_handler = MockHandler()

    # Configure ctxlog with our mock handler
    ctxlog.configure(level=LogLevel.INFO, handlers=[mock_handler])

    logger = ctxlog.get_logger("order_processor")

    # Create a parent log
    log = logger.new()
    log.event = "new_payment"
    log.ctx(payment_id="pay_123", amount=100.0, currency="USD")

    # Create chained logs
    validation_log = log.new(event="payment_validation")
    validation_log.ctx(transaction_id="txn_456")
    validation_log.info("Payment validation successful")

    notification_log = log.new(event="email_notification")
    notification_log.info("Email notification sent")

    business_log = log.new(event="business_logic")
    business_log.info("Business logic executed successfully")

    # Emit the parent log
    log.info("Payment processed successfully")

    # Check that we have one log entry
    assert len(mock_handler.logs) == 1

    # Get the log entry
    log_data = mock_handler.logs[0]

    # Check parent log
    assert log_data["level"] == "info"
    assert log_data["event"] == "new_payment"
    assert log_data["message"] == "Payment processed successfully"
    assert log_data["payment_id"] == "pay_123"
    assert log_data["amount"] == 100.0
    assert log_data["currency"] == "USD"

    # Check children
    assert len(log_data["children"]) == 3

    # Check validation log
    validation = log_data["children"][0]
    assert validation["level"] == "info"
    assert validation["event"] == "payment_validation"
    assert validation["message"] == "Payment validation successful"
    assert validation["transaction_id"] == "txn_456"

    # Check notification log
    notification = log_data["children"][1]
    assert notification["level"] == "info"
    assert notification["event"] == "email_notification"
    assert notification["message"] == "Email notification sent"

    # Check business log
    business = log_data["children"][2]
    assert business["level"] == "info"
    assert business["event"] == "business_logic"
    assert business["message"] == "Business logic executed successfully"


def test_file_handler():
    """Test logging to a file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "app.log")

        # Configure ctxlog with file handler
        ctxlog.configure(
            level=LogLevel.INFO,
            handlers=[
                ctxlog.FileHandler(
                    file_path=log_file,
                    serialize=True,
                )
            ],
        )

        logger = ctxlog.get_logger("test_module")
        logger.info("Test message")

        # Check that the file was created and contains the log
        assert os.path.exists(log_file)
        with open(log_file, "r") as f:
            log_data = json.loads(f.read())
            assert log_data["level"] == "info"
            assert log_data["message"] == "Test message"
