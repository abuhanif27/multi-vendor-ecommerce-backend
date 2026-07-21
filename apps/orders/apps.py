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
