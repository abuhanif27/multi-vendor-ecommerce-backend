import uuid
from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.shops.models import Shop, Product, ProductVariant
from apps.catalog.models import Category
from apps.inventory.models import Inventory
from apps.orders.models import Order, VendorOrder
from apps.shipping.models import Courier, Shipment, ShipmentTrackingEvent
from apps.shipping.services.shipping import ShippingService

User = get_user_model()

class ShippingModuleServiceTestCase(APITestCase):
    def setUp(self):
        # Buyer
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="password123",
            first_name="Buyer"
        )
        # Vendor
        self.vendor = User.objects.create_user(
            email="vendor@example.com",
            password="password123",
            first_name="Vendor",
            role="vendor"
        )
        
        self.category = Category.objects.create(name="Electronics")
        self.shop = Shop.objects.create(owner=self.vendor, name="Tech Store", status=Shop.ShopStatus.APPROVED)
        
        self.order = Order.objects.create(
            user=self.buyer,
            subtotal=100.00,
            grand_total=100.00,
            status=Order.OrderStatus.PENDING,
            shipping_address={"street": "123 Test St"}
        )
        
        self.vendor_order = VendorOrder.objects.create(
            order=self.order,
            shop=self.shop,
            vendor_total=100.00,
            status=VendorOrder.FulfillmentStatus.PENDING
        )
        
        self.courier = Courier.objects.create(
            name="Test Courier",
            tracking_url_template="https://test.com/track?id={tracking_number}"
        )
        
        # Ensure event subscription survives EventBus.clear() from other tests
        from apps.notifications.events import EventBus
        from apps.shipping.events import ShipmentDeliveredEvent
        from apps.orders.services.order import OrderService
        
        EventBus.subscribe(
            ShipmentDeliveredEvent,
            lambda event: OrderService.mark_vendor_order_delivered(event.vendor_order_id)
        )

    def test_initialize_shipment(self):
        """Test creating a shipment locks the correct status and creates a history event."""
        shipment = ShippingService.initialize_shipment(self.vendor_order.id)
        
        self.assertEqual(shipment.status, Shipment.ShipmentStatus.PENDING)
        self.assertEqual(shipment.shipping_address_snapshot, {"street": "123 Test St"})
        
        # Verify history was appended
        events = shipment.tracking_events.all()
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0].status, Shipment.ShipmentStatus.PENDING)

    def test_courier_assignment(self):
        """Test assigning a courier correctly resolves the Strategy Pattern template."""
        shipment = ShippingService.initialize_shipment(self.vendor_order.id)
        
        shipment = ShippingService.assign_courier(shipment.id, self.courier, "123456")
        
        self.assertEqual(shipment.tracking_number, "123456")
        self.assertEqual(shipment.tracking_url, "https://test.com/track?id=123456")

    def test_valid_fsm_transition(self):
        """Test progressing through the shipment lifecycle."""
        shipment = ShippingService.initialize_shipment(self.vendor_order.id)
        
        ShippingService.update_shipment_status(
            shipment.id, 
            Shipment.ShipmentStatus.SHIPPED, 
            location="Warehouse"
        )
        
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, Shipment.ShipmentStatus.SHIPPED)
        
        events = shipment.tracking_events.all()
        self.assertEqual(events.count(), 2)
        self.assertEqual(events[0].status, Shipment.ShipmentStatus.SHIPPED)
        self.assertEqual(events[0].location, "Warehouse")

    def test_invalid_fsm_transition_raises_error(self):
        """Test that skipping states or reversing illegally raises domain errors."""
        shipment = ShippingService.initialize_shipment(self.vendor_order.id)
        
        # Cannot go straight from PENDING to DELIVERED
        with self.assertRaises(ValidationError):
            ShippingService.update_shipment_status(
                shipment.id, 
                Shipment.ShipmentStatus.DELIVERED
            )
            
    def test_cod_delivery_completes_order_and_payment(self):
        """When the last shipment for a COD order is delivered, Payment should capture and Order complete."""
        # 1. Setup Payment
        from apps.payments.models import Payment
        payment = Payment.objects.create(
            order=self.order,
            provider=Payment.Provider.COD,
            amount=self.order.grand_total,
            status=Payment.PaymentStatus.PENDING,
            idempotency_key=uuid.uuid4()
        )
        
        # 2. Setup Shipment
        shipment = ShippingService.initialize_shipment(self.vendor_order.id)
        ShippingService.update_shipment_status(shipment.id, Shipment.ShipmentStatus.SHIPPED)
        ShippingService.update_shipment_status(shipment.id, Shipment.ShipmentStatus.OUT_FOR_DELIVERY)
        
        # 3. Mark Delivered
        ShippingService.update_shipment_status(shipment.id, Shipment.ShipmentStatus.DELIVERED)
        
        # 4. Assertions
        self.vendor_order.refresh_from_db()
        self.assertEqual(self.vendor_order.status, VendorOrder.FulfillmentStatus.DELIVERED)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.COMPLETED)
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.PaymentStatus.CAPTURED)
        self.assertEqual(payment.provider_reference, "COD_DELIVERED")

    def test_partial_shipment_delivery(self):
        """If one shipment delivers, VendorOrder shouldn't flip until all do."""
        # Create a second shipment for the same vendor order
        shipment1 = ShippingService.initialize_shipment(self.vendor_order.id)
        
        # Manually create another shipment (Simulating a split order)
        shipment2 = Shipment.objects.create(
            vendor_order=self.vendor_order,
            status=Shipment.ShipmentStatus.PENDING,
            shipping_address_snapshot={}
        )
        
        # Deliver shipment 1
        ShippingService.update_shipment_status(shipment1.id, Shipment.ShipmentStatus.READY_FOR_PICKUP)
        ShippingService.update_shipment_status(shipment1.id, Shipment.ShipmentStatus.SHIPPED)
        ShippingService.update_shipment_status(shipment1.id, Shipment.ShipmentStatus.OUT_FOR_DELIVERY)
        ShippingService.update_shipment_status(shipment1.id, Shipment.ShipmentStatus.DELIVERED)
        
        self.vendor_order.refresh_from_db()
        # Still PENDING because shipment2 is not delivered
        self.assertEqual(self.vendor_order.status, VendorOrder.FulfillmentStatus.PENDING)
        
        # Deliver shipment 2
        ShippingService.update_shipment_status(shipment2.id, Shipment.ShipmentStatus.SHIPPED)
        ShippingService.update_shipment_status(shipment2.id, Shipment.ShipmentStatus.OUT_FOR_DELIVERY)
        ShippingService.update_shipment_status(shipment2.id, Shipment.ShipmentStatus.DELIVERED)
        
        self.vendor_order.refresh_from_db()
        self.assertEqual(self.vendor_order.status, VendorOrder.FulfillmentStatus.DELIVERED)
