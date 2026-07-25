from abc import ABC, abstractmethod
from decimal import Decimal

class PaymentGateway(ABC):
    @abstractmethod
    def initialize_payment(self, payment_id: str, amount: Decimal, currency: str, customer_info: dict, return_url_base: str) -> str:
        """
        Initializes the payment with the gateway.
        Returns the URL to which the customer should be redirected.
        """
        pass

    @abstractmethod
    def validate_payment(self, payload: dict) -> dict:
        """
        Validates IPN/Callback payload with the gateway server.
        Returns validated data dictionary containing:
        - valid: bool
        - amount: Decimal
        - currency: str
        - raw_metadata: dict
        """
        pass

    @abstractmethod
    def refund_payment(self, refund_id: str, payment_id: str, amount: Decimal, bank_tran_id: str = None) -> dict:
        """
        Processes a refund via the gateway API.
        Returns data dictionary containing:
        - success: bool
        - raw_metadata: dict
        """
        pass
