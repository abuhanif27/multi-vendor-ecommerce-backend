from apps.payments.gateways.base import PaymentGateway
from apps.payments.models import Payment

class CashOnDeliveryGateway(PaymentGateway):
    """
    Internal Mock Gateway for Cash on Delivery.
    Bypasses external APIs and webhooks entirely.
    """

    def initialize_payment(self, payment_id: str, amount, currency: str, customer_info: dict, return_url_base: str) -> str:
        """
        Since there is no external checkout page, we just return a success signal.
        The frontend will immediately route the user to an "Order Placed" page.
        """
        payment = Payment.objects.get(id=payment_id)
        # Assign a mock reference
        payment.provider_reference = f"cod_{payment.id}"
        payment.payment_method = "cash"
        
        # NOTE: CoD remains PENDING until the driver marks it delivered.
        # OrderService will handle moving the Order to PROCESSING.
        payment.save(update_fields=['provider_reference', 'payment_method'])
        
        return ""

    def validate_payment(self, payload: dict) -> dict:
        """
        CoD does not use webhooks. This should never be called.
        """
        raise NotImplementedError("CoD does not support webhooks.")

    def refund_payment(self, refund_id: str, payment_id: str, amount, bank_tran_id: str = None) -> dict:
        """
        Refunds for CoD would involve manual cash returns or store credit.
        """
        raise NotImplementedError("Manual refund required for Cash on Delivery.")
