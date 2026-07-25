class PaymentGatewayError(Exception):
    """Base class for all payment gateway exceptions."""
    pass

class PaymentGatewayUnavailable(PaymentGatewayError):
    """Raised when the gateway is unreachable or times out."""
    pass

class PaymentValidationFailed(PaymentGatewayError):
    """Raised when a callback/IPN payload fails validation."""
    pass

class PaymentRefundFailed(PaymentGatewayError):
    """Raised when the gateway rejects a refund request."""
    pass

class PaymentInitializationFailed(PaymentGatewayError):
    """Raised when the gateway rejects a payment initialization request."""
    pass
