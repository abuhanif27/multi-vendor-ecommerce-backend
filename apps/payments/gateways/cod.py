from apps.payments.gateways.base import BaseGateway
from apps.payments.models import Payment

class CashOnDeliveryGateway(BaseGateway):
    """
    Internal Mock Gateway for Cash on Delivery.
    Bypasses external APIs and webhooks entirely.
    """

    def initialize_payment(self, payment):
        """
        Since there is no external checkout page, we just return a success signal.
        The frontend will immediately route the user to an "Order Placed" page.
        """
        # Assign a mock reference
        payment.provider_reference = f"cod_{payment.id}"
        payment.payment_method = "cash"
        
        # NOTE: CoD remains PENDING until the driver marks it delivered.
        # OrderService will handle moving the Order to PROCESSING.
        payment.save(update_fields=['provider_reference', 'payment_method'])
        
        return {
            "checkout_url": None,
            "status": "success",
            "message": "Cash on Delivery initialized."
        }

    def verify_webhook(self, request):
        """
        CoD does not use webhooks. This should never be called.
        """
        raise NotImplementedError("CoD does not support webhooks.")

    def refund_payment(self, payment, amount=None):
        """
        Refunds for CoD would involve manual cash returns or store credit.
        """
        raise NotImplementedError("Manual refund required for Cash on Delivery.")
