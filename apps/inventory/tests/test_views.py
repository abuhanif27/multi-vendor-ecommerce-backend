from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apps.catalog.models import Category
from apps.shops.models import Shop, Product, ProductVariant
from apps.inventory.models import Inventory

User = get_user_model()


class InventoryDetailAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="password")
        if hasattr(self.owner, "role"):
            self.owner.role = "vendor"
            self.owner.save()
            
        self.other_user = User.objects.create_user(email="other@example.com", password="password")

        self.shop = Shop.objects.create(owner=self.owner, name="Owner Shop", status=Shop.ShopStatus.APPROVED)
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(shop=self.shop, category=self.category, name="Test Product", status=Product.ProductStatus.ACTIVE)
        
        # VariantService normally creates inventory, but we bypass for testing models directly
        self.variant = ProductVariant.objects.create(product=self.product, sku="TEST-SKU", price=15.0)
        self.inventory = Inventory.objects.create(variant=self.variant, quantity_on_hand=100)

        self.url = reverse("inventory-detail", kwargs={
            "shop_slug": self.shop.slug,
            "product_slug": self.product.slug,
            "sku": self.variant.sku,
        })

    def test_owner_can_view_inventory(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["quantity_on_hand"], 100)
        self.assertEqual(response.json()["available_quantity"], 100)

    def test_other_cannot_view_inventory(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
