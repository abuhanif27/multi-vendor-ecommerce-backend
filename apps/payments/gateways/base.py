from abc import ABC, abstractmethod

class BaseGateway(ABC):
    """
    Abstract Base Class for all payment gateways.
    Enforces a strict interface that all providers must implement.
    """

    @abstractmethod
    def initialize_payment(self, payment):
        """
        Calls the external provider to generate a payment session or intent.
        Returns a dictionary containing necessary frontend data, e.g.,
        {"checkout_url": "https://...", "client_secret": "..."}
        """
        pass

    @abstractmethod
    def verify_webhook(self, request):
        """
        Verifies the cryptographic signature of the incoming webhook.
        Parses the payload and returns a standardized dictionary:
        {"status": "CAPTURED", "provider_reference": "xxx", "amount": 100.00}
        """
        pass

    @abstractmethod
    def refund_payment(self, payment, amount=None):
        """
        Initiates a refund via the provider API.
        """
        pass
