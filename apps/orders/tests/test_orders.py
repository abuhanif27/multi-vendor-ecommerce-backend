from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.shops.models import Shop, Product, ProductVariant
from apps.catalog.models import Category
from apps.inventory.models import Inventory
from apps.cart.services.cart import CartService
from apps.checkout.services.checkout import CheckoutService
from apps.orders.models import Order, VendorOrder, OrderItem
from apps.orders.services.order import OrderService

User = get_user_model()

class OrderModuleAPITestCase(APITestCase):
    def setUp(self):
        # Buyer
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="password123",
            first_name="Buyer"
        )
        # Vendor 1
        self.vendor1 = User.objects.create_user(
            email="vendor1@example.com",
            password="password123",
            first_name="Vendor1",
            role="vendor"
        )
        # Vendor 2
        self.vendor2 = User.objects.create_user(
            email="vendor2@example.com",
            password="password123",
            first_name="Vendor2",
            role="vendor"
        )
        
        self.category = Category.objects.create(name="Electronics")
        
        # Shop 1
        self.shop1 = Shop.objects.create(owner=self.vendor1, name="Tech Store", status=Shop.ShopStatus.APPROVED)
        self.product1 = Product.objects.create(shop=self.shop1, category=self.category, name="Laptop", status=Product.ProductStatus.ACTIVE)
        self.variant1 = ProductVariant.objects.create(product=self.product1, sku="LAP-1", price=1000.00, status=ProductVariant.VariantStatus.ACTIVE)
        self.inventory1 = Inventory.objects.create(variant=self.variant1, quantity_on_hand=50)
        
        # Shop 2
        self.shop2 = Shop.objects.create(owner=self.vendor2, name="Audio Store", status=Shop.ShopStatus.APPROVED)
        self.product2 = Product.objects.create(shop=self.shop2, category=self.category, name="Headphones", status=Product.ProductStatus.ACTIVE)
        self.variant2 = ProductVariant.objects.create(product=self.product2, sku="HEAD-1", price=200.00, status=ProductVariant.VariantStatus.ACTIVE)
        self.inventory2 = Inventory.objects.create(variant=self.variant2, quantity_on_hand=20)
        
        # Build cart for buyer
        CartService.add_item(self.buyer, "LAP-1", 1)
        CartService.add_item(self.buyer, "HEAD-1", 2)
        
        # Run checkout to generate the order
        self.order = CheckoutService.process_checkout(
            user=self.buyer,
            shipping_address={"street": "123"},
            billing_address={"street": "123"}
        )

    def test_order_creation_boundaries(self):
        """Test that Checkout correctly instantiated multi-vendor orders"""
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(VendorOrder.objects.count(), 2)
        self.assertEqual(OrderItem.objects.count(), 2)
        
        self.assertEqual(self.order.grand_total, 1400.00)

    def test_buyer_order_list_api(self):
        """Buyer should see their aggregated order"""
        self.client.force_authenticate(user=self.buyer)
        url = reverse("order-list")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data.get("results", data)
        self.assertEqual(len(results), 1)
        self.assertEqual(float(results[0]["grand_total"]), 1400.00)
        self.assertEqual(len(results[0]["vendor_orders"]), 2)

    def test_vendor_order_list_isolation(self):
        """Vendor 1 should ONLY see their slice of the order"""
        self.client.force_authenticate(user=self.vendor1)
        url = reverse("vendor-order-list")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data.get("results", data)
        self.assertEqual(len(results), 1)
        
        vendor_order = results[0]
        self.assertEqual(vendor_order["shop_name"], "Tech Store")
        self.assertEqual(float(vendor_order["vendor_total"]), 1000.00)
        
        # Verify they cannot see Vendor2's items
        self.assertEqual(len(vendor_order["items"]), 1)
        self.assertEqual(vendor_order["items"][0]["sku"], "LAP-1")

    def test_cancel_order_releases_inventory(self):
        """Cancelling an order should release locks immediately"""
        # Initially locked
        self.inventory1.refresh_from_db()
        self.assertEqual(self.inventory1.quantity_reserved, 1)
        
        # Cancel order
        OrderService.cancel_order(self.order.id)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.CANCELLED)
        
        # Check sub-orders cancelled
        vendor_orders = self.order.vendor_orders.all()
        for vo in vendor_orders:
            self.assertEqual(vo.status, VendorOrder.FulfillmentStatus.CANCELLED)
            
        # Check inventory released
        self.inventory1.refresh_from_db()
        self.assertEqual(self.inventory1.quantity_reserved, 0)
