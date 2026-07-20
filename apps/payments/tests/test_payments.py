from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.shops.models import Shop, Product, ProductVariant
from apps.catalog.models import Category
from apps.inventory.models import Inventory
from apps.cart.services.cart import CartService
from apps.checkout.services.checkout import CheckoutService
from apps.orders.models import Order, VendorOrder
from apps.payments.models import Payment
from apps.payments.services.payment import PaymentService
import uuid

User = get_user_model()

class PaymentModuleAPITestCase(APITestCase):
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
        self.product = Product.objects.create(shop=self.shop, category=self.category, name="Laptop", status=Product.ProductStatus.ACTIVE)
        self.variant = ProductVariant.objects.create(product=self.product, sku="LAP-1", price=1000.00, status=ProductVariant.VariantStatus.ACTIVE)
        self.inventory = Inventory.objects.create(variant=self.variant, quantity_on_hand=50)
        
        # Build cart for buyer
        CartService.add_item(self.buyer, "LAP-1", 1)
        
        # Run checkout to generate the order
        self.order = CheckoutService.process_checkout(
            user=self.buyer,
            shipping_address={"street": "123"},
            billing_address={"street": "123"}
        )

    def test_cod_initialization_flow(self):
        """Testing Cash on Delivery bypasses webhooks and goes to PROCESSING"""
        self.client.force_authenticate(user=self.buyer)
        url = reverse("payment-create")
        
        response = self.client.post(url, {
            "order_id": str(self.order.id),
            "provider": Payment.Provider.COD
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check Payment Ledger
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.provider, Payment.Provider.COD)
        self.assertEqual(payment.status, Payment.PaymentStatus.PENDING) # CoD remains pending
        
        # Check Order Status
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.PENDING)
        
        # Verify VendorOrders were bumped to PROCESSING so they can ship
        vendor_order = self.order.vendor_orders.first()
        self.assertEqual(vendor_order.status, VendorOrder.FulfillmentStatus.PROCESSING)

    def test_webhook_success_flow(self):
        """Testing what happens when Stripe sends a success webhook"""
        # Manually create a pending mock Stripe payment
        payment = Payment.objects.create(
            order=self.order,
            provider=Payment.Provider.STRIPE,
            amount=self.order.grand_total,
            status=Payment.PaymentStatus.PENDING,
            idempotency_key=uuid.uuid4()
        )
        
        # Simulate the Stripe webhook hitting the service
        PaymentService.process_webhook_success(
            payment_id=payment.id,
            provider_reference="pi_12345",
            raw_metadata={"foo": "bar"}
        )
        
        # Assert Payment
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.PaymentStatus.CAPTURED)
        self.assertEqual(payment.provider_reference, "pi_12345")
        
        # Assert Order cascaded to PAID
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.PAID)
        
        # Assert VendorOrder cascaded to PROCESSING
        vendor_order = self.order.vendor_orders.first()
        self.assertEqual(vendor_order.status, VendorOrder.FulfillmentStatus.PROCESSING)

    def test_webhook_failure_flow_releases_inventory(self):
        """Testing what happens when a payment fails"""
        # Initially locked
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_reserved, 1)
        
        payment = Payment.objects.create(
            order=self.order,
            provider=Payment.Provider.STRIPE,
            amount=self.order.grand_total,
            status=Payment.PaymentStatus.PENDING,
            idempotency_key=uuid.uuid4()
        )
        
        # Simulate Webhook Failure
        PaymentService.process_webhook_failure(
            payment_id=payment.id,
            failure_reason="Insufficient Funds",
            raw_metadata={"declined": True}
        )
        
        # Assert Payment
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.PaymentStatus.FAILED)
        self.assertEqual(payment.failure_reason, "Insufficient Funds")
        
        # Assert Order cascaded to CANCELLED
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.CANCELLED)
        
        # Assert Inventory was RELEASED automatically
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_reserved, 0)
