import uuid
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.orders.models import Order
from apps.payments.models import Payment
from apps.payments.gateways.cod import CashOnDeliveryGateway
# from apps.payments.gateways.stripe import StripeGateway  # (Future integration)

class PaymentService:
    """
    Orchestrates the selection of payment gateways and handles internal payment records.
    """

    @staticmethod
    def _get_gateway(provider):
        if provider == Payment.Provider.COD:
            return CashOnDeliveryGateway()
        # elif provider == Payment.Provider.STRIPE:
        #     return StripeGateway()
        raise NotImplementedError(f"Gateway for {provider} is not implemented.")

    @staticmethod
    @transaction.atomic
    def initialize_payment(order_id, provider):
        """
        Creates a PENDING payment record and calls the external gateway to initialize the session.
        """
        order = Order.objects.get(id=order_id)
        
        if order.status != Order.OrderStatus.PENDING:
            raise ValidationError(f"Order is {order.status}, cannot initialize payment.")
            
        # Optional: Cancel any previous pending payments for this order to prevent duplicate intents
        Payment.objects.filter(order=order, status=Payment.PaymentStatus.PENDING).update(status=Payment.PaymentStatus.FAILED, failure_reason="Superceded by new payment attempt")
        
        # 1. Create the Payment Ledger Record
        payment = Payment.objects.create(
            order=order,
            provider=provider,
            amount=order.grand_total,
            idempotency_key=uuid.uuid4()
        )
        
        # 2. Call the Strategy
        gateway = PaymentService._get_gateway(provider)
        response_data = gateway.initialize_payment(payment)
        
        # 3. Handle CoD Special Case (Bypasses webhook)
        if provider == Payment.Provider.COD:
            # Tell OrderService to start processing immediately without waiting for CAPTURED
            from apps.orders.services.order import OrderService
            OrderService.mark_order_processing(order.id)
            
        return response_data

    @staticmethod
    @transaction.atomic
    def process_webhook_success(payment_id, provider_reference, raw_metadata):
        """
        Called by the webhook view when a payment succeeds.
        Guaranteed to be idempotent.
        """
        # Lock the row to prevent race conditions from duplicate webhooks
        payment = Payment.objects.select_for_update().get(id=payment_id)
        
        if payment.status == Payment.PaymentStatus.CAPTURED:
            # Idempotency safety: already processed
            return payment
            
        payment.status = Payment.PaymentStatus.CAPTURED
        payment.paid_at = timezone.now()
        payment.provider_reference = provider_reference
        payment.raw_metadata = raw_metadata
        payment.save(update_fields=['status', 'paid_at', 'provider_reference', 'raw_metadata'])
        
        # Trigger downstream logic
        from apps.orders.services.order import OrderService
        OrderService.mark_order_paid(payment.order.id)
        
        return payment

    @staticmethod
    @transaction.atomic
    def process_webhook_failure(payment_id, failure_reason, raw_metadata):
        payment = Payment.objects.select_for_update().get(id=payment_id)
        
        if payment.status in [Payment.PaymentStatus.CAPTURED, Payment.PaymentStatus.FAILED]:
            return payment
            
        payment.status = Payment.PaymentStatus.FAILED
        payment.failure_reason = failure_reason
        payment.raw_metadata = raw_metadata
        payment.save(update_fields=['status', 'failure_reason', 'raw_metadata'])
        
        from apps.orders.services.order import OrderService
        OrderService.cancel_order(payment.order.id)
        
        return payment

    @staticmethod
    @transaction.atomic
    def capture_cod_payment(order_id):
        """
        Internal business logic hook.
        Triggered when ShippingService reports that the order was successfully delivered.
        """
        payment = Payment.objects.select_for_update().get(order_id=order_id, provider=Payment.Provider.COD)
        
        if payment.status == Payment.PaymentStatus.CAPTURED:
            return payment
            
        payment.status = Payment.PaymentStatus.CAPTURED
        payment.paid_at = timezone.now()
        payment.provider_reference = "COD_DELIVERED"
        payment.save(update_fields=['status', 'paid_at', 'provider_reference'])
        
        return payment

    @staticmethod
    @transaction.atomic
    def process_refund(payment_id: str, amount, reason_code: str, admin_notes: str = "", vendor_order_id: str = None, actor=None):
        """
        Process a partial or full refund for a payment.
        """
        payment = Payment.objects.select_for_update().get(id=payment_id)
        
        if payment.status != Payment.PaymentStatus.CAPTURED:
            raise ValidationError("Only captured payments can be refunded.")
            
        from apps.payments.models import Refund, RefundStatus
        from django.db.models import Sum
        from decimal import Decimal
        
        # Calculate available refund amount
        successful_refunds = payment.refunds.filter(
            status__in=[RefundStatus.SUCCEEDED, RefundStatus.PENDING]
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        amount_decimal = Decimal(str(amount))
        if amount_decimal > (payment.amount - successful_refunds):
            raise ValidationError("Refund amount exceeds available payment balance.")
            
        # Create PENDING Refund record
        refund = Refund.objects.create(
            payment=payment,
            vendor_order_id=vendor_order_id,
            amount=amount_decimal,
            reason_code=reason_code,
            admin_notes=admin_notes,
            status=RefundStatus.PENDING,
            idempotency_key=uuid.uuid4()
        )
        
        # Call Gateway
        gateway = PaymentService._get_gateway(payment.provider)
        try:
            gateway_resp = gateway.refund_payment(payment, amount_decimal)
            refund.status = RefundStatus.SUCCEEDED
            if gateway_resp and 'provider_reference' in gateway_resp:
                refund.provider_reference = gateway_resp['provider_reference']
        except NotImplementedError:
            # Fallback for gateways that don't support automated refunds (e.g. COD)
            refund.status = RefundStatus.SUCCEEDED
            refund.provider_reference = "MANUAL_REFUND"
        except Exception as e:
            refund.status = RefundStatus.FAILED
            refund.raw_metadata = {"error": str(e)}
            
        refund.save()
        
        # Log Audit Action if actor provided
        if actor:
            from apps.administration.services.audit import AuditService
            AuditService.log_action(
                actor=actor,
                action="REFUND",
                resource_type="Payment",
                resource_id=str(payment.id),
                result="SUCCESS" if refund.status == RefundStatus.SUCCEEDED else "FAILED",
                after_state={"refund_id": str(refund.id), "amount": str(refund.amount)},
                reason=reason_code
            )
        
        if refund.status == RefundStatus.SUCCEEDED:
            from apps.payments.events import PaymentRefundedEvent
            from apps.notifications.events import EventBus
            
            event = PaymentRefundedEvent(
                refund_id=str(refund.id),
                payment_id=str(payment.id),
                vendor_order_id=str(vendor_order_id) if vendor_order_id else None,
                amount=str(refund.amount),
                status=refund.status,
                occurred_at=timezone.now()
            )
            transaction.on_commit(lambda: EventBus.publish(event))
            
        return refund
