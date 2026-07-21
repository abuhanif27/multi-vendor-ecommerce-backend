from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.orders.models import VendorOrder, OrderItem, Return, ReturnItem, ReturnStatus
from apps.notifications.events import EventBus
from apps.orders.events import ReturnRequestedEvent, ReturnApprovedEvent, ReturnRejectedEvent, ReturnReceivedEvent

class ReturnService:
    @staticmethod
    @transaction.atomic
    def request_return(vendor_order_id: str, items: list[dict], reason: str):
        """
        Customer initiates a return.
        items: [{"order_item_id": str, "quantity": int}]
        """
        vendor_order = VendorOrder.objects.get(id=vendor_order_id)
        
        if vendor_order.status != VendorOrder.FulfillmentStatus.DELIVERED:
            raise ValidationError("Returns can only be requested for DELIVERED orders.")
            
        if not items:
            raise ValidationError("Must provide at least one item to return.")
            
        # Create Return record
        return_req = Return.objects.create(
            vendor_order=vendor_order,
            reason=reason,
            status=ReturnStatus.REQUESTED
        )
        
        for item_data in items:
            order_item_id = item_data['order_item_id']
            quantity = item_data['quantity']
            
            order_item = OrderItem.objects.get(id=order_item_id, vendor_order=vendor_order)
            
            # Validate quantity against purchased and previously returned amounts
            from django.db.models import Sum
            already_returned = ReturnItem.objects.filter(
                order_item=order_item,
                return_request__status__in=[
                    ReturnStatus.REQUESTED, ReturnStatus.APPROVED, 
                    ReturnStatus.SHIPPED, ReturnStatus.RECEIVED
                ]
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0
            
            if quantity + already_returned > order_item.quantity:
                raise ValidationError(f"Cannot return {quantity} of {order_item.product_name}. Exceeds purchased quantity.")
                
            ReturnItem.objects.create(
                return_request=return_req,
                order_item=order_item,
                quantity=quantity
            )
            
        # Integration Event (Async notification to Vendor)
        event = ReturnRequestedEvent(
            return_id=str(return_req.id),
            vendor_order_id=str(vendor_order.id),
            occurred_at=timezone.now()
        )
        transaction.on_commit(lambda: EventBus.publish(event))
        
        return return_req

    @staticmethod
    @transaction.atomic
    def approve_return(return_id: str, actor):
        """
        Vendor approves the return.
        """
        return_req = Return.objects.select_for_update().get(id=return_id)
        
        if return_req.status != ReturnStatus.REQUESTED:
            raise ValidationError("Only REQUESTED returns can be approved.")
            
        return_req.status = ReturnStatus.APPROVED
        return_req.save(update_fields=['status'])
        
        # Integration Event (Async notification to Customer)
        event = ReturnApprovedEvent(
            return_id=str(return_req.id),
            vendor_order_id=str(return_req.vendor_order.id),
            actor_id=actor.id,
            occurred_at=timezone.now()
        )
        transaction.on_commit(lambda: EventBus.publish(event))
        
        return return_req

    @staticmethod
    @transaction.atomic
    def reject_return(return_id: str, actor, reason: str):
        """
        Vendor rejects the return.
        """
        return_req = Return.objects.select_for_update().get(id=return_id)
        
        if return_req.status != ReturnStatus.REQUESTED:
            raise ValidationError("Only REQUESTED returns can be rejected.")
            
        return_req.status = ReturnStatus.REJECTED
        return_req.save(update_fields=['status'])
        
        # Integration Event (Async notification to Customer)
        event = ReturnRejectedEvent(
            return_id=str(return_req.id),
            vendor_order_id=str(return_req.vendor_order.id),
            actor_id=actor.id,
            reason=reason,
            occurred_at=timezone.now()
        )
        transaction.on_commit(lambda: EventBus.publish(event))
        
        return return_req

    @staticmethod
    @transaction.atomic
    def mark_return_received(return_id: str, actor):
        """
        Vendor confirms receipt of the returned items.
        Triggers Inventory Restock synchronously (Domain Event pattern).
        """
        return_req = Return.objects.select_for_update().get(id=return_id)
        
        if return_req.status not in [ReturnStatus.APPROVED, ReturnStatus.SHIPPED]:
            raise ValidationError("Return must be APPROVED or SHIPPED to be marked as RECEIVED.")
            
        return_req.status = ReturnStatus.RECEIVED
        return_req.save(update_fields=['status'])
        
        # Domain Event: Published synchronously to ensure Inventory updates
        # execute within the same transaction. If inventory fails, the return fails.
        event = ReturnReceivedEvent(
            return_id=str(return_req.id),
            vendor_order_id=str(return_req.vendor_order.id),
            actor_id=actor.id,
            occurred_at=timezone.now()
        )
        EventBus.publish(event)
        
        return return_req
