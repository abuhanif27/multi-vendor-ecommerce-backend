from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.shops.models import Shop, Product, ProductVariant
from apps.catalog.models import Category
from apps.inventory.models import Inventory
from apps.cart.models import Cart, CartItem
from apps.cart.services.cart import CartService

User = get_user_model()

class CartAPITestCase(APITestCase):
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
        
        # Add inventory
        self.inventory = Inventory.objects.create(
            variant=self.variant,
            quantity_on_hand=50,
        )
        
        self.client.force_authenticate(user=self.user)
        self.cart_url = reverse("cart-detail")
        self.items_url = reverse("cart-items")

    def test_get_cart_creates_implicitly(self):
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.status, Cart.CartStatus.ACTIVE)

    def test_add_item_to_cart(self):
        response = self.client.post(self.items_url, {"sku": "LAPTOP-8GB", "quantity": 2})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        item = cart.items.first()
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, 1000.00)

    def test_add_duplicate_item_increments_quantity(self):
        self.client.post(self.items_url, {"sku": "LAPTOP-8GB", "quantity": 2})
        response = self.client.post(self.items_url, {"sku": "LAPTOP-8GB", "quantity": 3})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 5)

    def test_inventory_validation(self):
        response = self.client.post(self.items_url, {"sku": "LAPTOP-8GB", "quantity": 60})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Insufficient stock", response.data["detail"][0])

    def test_update_item_quantity(self):
        self.client.post(self.items_url, {"sku": "LAPTOP-8GB", "quantity": 2})
        item = Cart.objects.get(user=self.user).items.first()
        
        url = reverse("cart-item-detail", kwargs={"pk": item.id})
        response = self.client.patch(url, {"quantity": 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 10)

    def test_remove_item(self):
        self.client.post(self.items_url, {"sku": "LAPTOP-8GB", "quantity": 2})
        item = Cart.objects.get(user=self.user).items.first()
        
        url = reverse("cart-item-detail", kwargs={"pk": item.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Cart.objects.get(user=self.user).items.count(), 0)

    def test_clear_cart(self):
        self.client.post(self.items_url, {"sku": "LAPTOP-8GB", "quantity": 2})
        response = self.client.delete(self.items_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Cart.objects.get(user=self.user).items.count(), 0)

    def test_totals_calculation(self):
        self.client.post(self.items_url, {"sku": "LAPTOP-8GB", "quantity": 2})
        
        response = self.client.get(self.cart_url)
        data = response.data
        
        self.assertEqual(data["cart_total"], 2000.00)
        self.assertEqual(data["items"][0]["item_total"], 2000.00)
        
        # Test price update snapshot
        self.variant.price = 1200.00
        self.variant.save()
        
        # In CartRetrieveAPIView we use live price for totals calculation (variant.price * quantity)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.data["cart_total"], 2400.00)

    def test_validate_cart_catches_price_change(self):
        self.client.post(self.items_url, {"sku": "LAPTOP-8GB", "quantity": 2})
        
        self.variant.price = 1200.00
        self.variant.save()
        
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as context:
            CartService.validate_cart(self.user)
            
        self.assertIn("Price for LAPTOP-8GB has changed", str(context.exception))
