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
            # Check total items ordered vs total items returned (across all received returns)
            # Simplified for Phase 2: If we want to mark VendorOrder as RETURNED
            pass
            
        EventBus.subscribe(
            ReturnReceivedEvent,
            handle_return_received
        )
