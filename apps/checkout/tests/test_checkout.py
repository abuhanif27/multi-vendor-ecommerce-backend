from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.shops.models import Shop, Product, ProductVariant
from apps.catalog.models import Category
from apps.inventory.models import Inventory
from apps.cart.models import CartItem
from apps.cart.services.cart import CartService

User = get_user_model()

class CheckoutAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="buyer@example.com",
            password="password123",
            first_name="Buyer"
        )
        self.vendor = User.objects.create_user(
            email="vendor@example.com",
            password="password123",
            first_name="Vendor"
        )
        
        self.category = Category.objects.create(name="Electronics")
        self.shop = Shop.objects.create(owner=self.vendor, name="Tech Store", status=Shop.ShopStatus.APPROVED)
        self.product = Product.objects.create(shop=self.shop, category=self.category, name="Laptop", status=Product.ProductStatus.ACTIVE)
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="LAPTOP-8GB",
            price=1000.00,
            status=ProductVariant.VariantStatus.ACTIVE
        )
        
        self.inventory = Inventory.objects.create(
            variant=self.variant,
            quantity_on_hand=50,
        )
        
        self.client.force_authenticate(user=self.user)
        self.checkout_url = reverse("checkout")

    def test_checkout_summary_empty_cart(self):
        # Implicitly creates an active cart if one does not exist
        CartService.get_or_create_cart(self.user)
        
        response = self.client.get(self.checkout_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cart is empty", response.data["detail"][0])

    def test_checkout_summary_success(self):
        CartService.add_item(self.user, "LAPTOP-8GB", 2)
        
        response = self.client.get(self.checkout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(float(data["subtotal"]), 2000.00)
        self.assertEqual(float(data["total"]), 2000.00)
        self.assertEqual(len(data["warnings"]["inventory"]), 0)

    def test_checkout_summary_inventory_warning(self):
        # Buy 40 first
        CartService.add_item(self.user, "LAPTOP-8GB", 40)
        
        # Someone else buys 20
        self.inventory.quantity_on_hand = 30
        self.inventory.save()
        
        response = self.client.get(self.checkout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data["warnings"]["inventory"]), 1)
        self.assertEqual(len(data["warnings"]["unavailable_items"]), 1)
        self.assertIn("Insufficient stock", data["warnings"]["inventory"][0])

    def test_checkout_summary_price_warning(self):
        CartService.add_item(self.user, "LAPTOP-8GB", 2)
        
        # Vendor increases price
        self.variant.price = 1200.00
        self.variant.save()
        
        response = self.client.get(self.checkout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(float(data["subtotal"]), 2400.00)  # Uses live price
        self.assertEqual(len(data["warnings"]["price"]), 1)
        self.assertIn("changed", data["warnings"]["price"][0])

    def test_checkout_process_success(self):
        CartService.add_item(self.user, "LAPTOP-8GB", 2)
        
        payload = {
            "shipping_address": {
                "street": "123 Main St",
                "city": "Metropolis",
                "state": "NY",
                "postal_code": "10001",
                "country": "USA"
            }
        }
        
        response = self.client.post(self.checkout_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that cart is now CHECKED_OUT
        from apps.cart.models import Cart
        cart = Cart.objects.get(user=self.user, status=Cart.CartStatus.CHECKED_OUT)
        self.assertIsNotNone(cart)
        
        # Check that order was created
        from apps.orders.models import Order
        order = Order.objects.get(id=response.data["order_id"])
        self.assertEqual(order.status, Order.OrderStatus.PENDING)
        self.assertEqual(order.vendor_orders.count(), 1)
        self.assertEqual(order.vendor_orders.first().items.count(), 1)
        
        # Check that inventory was reserved
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_reserved, 2)
        self.assertEqual(self.inventory.quantity_on_hand, 50)
        
    def test_checkout_process_fails_on_warning(self):
        CartService.add_item(self.user, "LAPTOP-8GB", 2)
        
        # Vendor increases price
        self.variant.price = 1200.00
        self.variant.save()
        
        payload = {
            "shipping_address": {
                "street": "123 Main St",
                "city": "Metropolis",
                "state": "NY",
                "postal_code": "10001",
                "country": "USA"
            }
        }
        
        response = self.client.post(self.checkout_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("prices have changed", response.data["detail"][0])
        
        # Inventory should NOT be reserved
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_reserved, 0)
