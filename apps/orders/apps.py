from django.apps import AppConfig

class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'Orders'

    def ready(self):
        from apps.notifications.events import EventBus
        from apps.shipping.events import ShipmentDeliveredEvent
        from apps.orders.services.order import OrderService
        
        EventBus.subscribe(
            ShipmentDeliveredEvent,
            lambda event: OrderService.mark_vendor_order_delivered(event.vendor_order_id)
        )
        
        from apps.payments.events import PaymentRefundedEvent
        EventBus.subscribe(
            PaymentRefundedEvent,
            lambda event: OrderService.process_refund_event(event)
        )
        
        from apps.orders.events import ReturnReceivedEvent
        from apps.orders.models import Return
        from apps.inventory.services.inventory import InventoryService
        
        def handle_return_received(event):
            from django.db.models import Sum
            return_req = Return.objects.prefetch_related('items__order_item__variant').get(id=event.return_id)
            for item in return_req.items.all():
                if item.order_item.variant:
                    InventoryService.restock_inventory(
                        variant_id=item.order_item.variant.id,
                        quantity=item.quantity,
                        reference=f"Return {return_req.id}"
                    )
            
            # Check if all items are returned
            vendor_order = return_req.vendor_order
            total_purchased = vendor_order.items.aggregate(Sum('quantity'))['quantity__sum'] or 0
            
            total_returned = ReturnItem.objects.filter(
                return_request__vendor_order=vendor_order,
                return_request__status=ReturnStatus.RECEIVED
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0
            
            if total_returned >= total_purchased:
                vendor_order.status = VendorOrder.FulfillmentStatus.RETURNED
            else:
                vendor_order.status = VendorOrder.FulfillmentStatus.PARTIALLY_RETURNED
                
            vendor_order.save(update_fields=['status'])
            
        EventBus.subscribe(
            ReturnReceivedEvent,
            handle_return_received
        )
