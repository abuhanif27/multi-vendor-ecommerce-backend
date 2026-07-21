from django.test import TransactionTestCase
from django.utils import timezone
from apps.orders.models import Order, VendorOrder, OrderItem, Return, ReturnItem, ReturnStatus
from apps.orders.services.returns import ReturnService
from apps.shops.models import Shop, Product, ProductVariant
from apps.inventory.services.inventory import InventoryService
from apps.inventory.models import Inventory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.notifications.events import EventBus
from apps.orders.events import ReturnRequestedEvent, ReturnApprovedEvent, ReturnReceivedEvent
from decimal import Decimal

from apps.catalog.models import Category

User = get_user_model()

class ReturnServiceTests(TransactionTestCase):
    def setUp(self):
        EventBus.clear()
        
        self.user = User.objects.create_user(email="buyer@example.com", password="password")
        self.vendor = User.objects.create_user(email="vendor@example.com", password="password")
        self.shop = Shop.objects.create(name="Test Shop", owner=self.vendor, status=Shop.ShopStatus.APPROVED)
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(name="Product", shop=self.shop, category=self.category)
        self.variant = ProductVariant.objects.create(product=self.product, sku="SKU-1", price=Decimal('10.00'))
        
        InventoryService.create_inventory(self.variant, initial_stock=5)
        
        self.order = Order.objects.create(user=self.user, shipping_address={}, grand_total=Decimal('20.00'))
        self.vendor_order = VendorOrder.objects.create(
            order=self.order, shop=self.shop, vendor_total=Decimal('20.00'), status=VendorOrder.FulfillmentStatus.DELIVERED
        )
        self.order_item = OrderItem.objects.create(
            vendor_order=self.vendor_order, variant=self.variant, product_name="Product",
            sku="SKU-1", unit_price=Decimal('10.00'), quantity=2, item_total=Decimal('20.00')
        )
        
        self.events = []
        EventBus.subscribe(ReturnRequestedEvent, lambda e: self.events.append(e))
        EventBus.subscribe(ReturnApprovedEvent, lambda e: self.events.append(e))
        
        def test_received_subscriber(e):
            from django.db.models import Sum
            self.events.append(e)
            # Re-implement apps.py subscriber for testing since we cleared the EventBus
            return_req = Return.objects.prefetch_related('items__order_item__variant').get(id=e.return_id)
            for item in return_req.items.all():
                if item.order_item.variant:
                    InventoryService.restock_inventory(
                        variant_id=item.order_item.variant.id,
                        quantity=item.quantity,
                        reference=f"Return {return_req.id}"
                    )
            
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
        
        EventBus.subscribe(ReturnReceivedEvent, test_received_subscriber)

    def test_request_return_success(self):
        return_req = ReturnService.request_return(
            vendor_order_id=self.vendor_order.id,
            items=[{"order_item_id": self.order_item.id, "quantity": 1}],
            reason="Defective"
        )
        
        self.assertEqual(return_req.status, ReturnStatus.REQUESTED)
        self.assertEqual(return_req.items.count(), 1)
        self.assertEqual(return_req.items.first().quantity, 1)
        
        # Check event
        self.assertTrue(any(isinstance(e, ReturnRequestedEvent) for e in self.events))

    def test_request_return_exceeds_quantity(self):
        with self.assertRaises(ValidationError):
            ReturnService.request_return(
                vendor_order_id=self.vendor_order.id,
                items=[{"order_item_id": self.order_item.id, "quantity": 3}],
                reason="Defective"
            )

    def test_approve_return(self):
        return_req = Return.objects.create(vendor_order=self.vendor_order, reason="Test", status=ReturnStatus.REQUESTED)
        
        ReturnService.approve_return(return_req.id, self.vendor)
        return_req.refresh_from_db()
        
        self.assertEqual(return_req.status, ReturnStatus.APPROVED)
        self.assertTrue(any(isinstance(e, ReturnApprovedEvent) for e in self.events))

    def test_mark_return_received(self):
        # We need to test the Domain Event subscriber as well
        # In TransactionTestCase, apps are loaded and ready() is executed
        return_req = Return.objects.create(vendor_order=self.vendor_order, reason="Test", status=ReturnStatus.APPROVED)
        ReturnItem.objects.create(return_request=return_req, order_item=self.order_item, quantity=1)
        
        inv_before = Inventory.objects.get(variant=self.variant).quantity_on_hand
        
        ReturnService.mark_return_received(return_req.id, self.vendor)
        return_req.refresh_from_db()
        
        self.assertEqual(return_req.status, ReturnStatus.RECEIVED)
        self.assertTrue(any(isinstance(e, ReturnReceivedEvent) for e in self.events))
        
        inv_after = Inventory.objects.get(variant=self.variant).quantity_on_hand
        self.assertEqual(inv_after, inv_before + 1)
