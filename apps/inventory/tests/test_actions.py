from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apps.catalog.models import Category
from apps.shops.models import Shop, Product, ProductVariant
from apps.inventory.models import Inventory, InventoryTransaction

User = get_user_model()


class InventoryActionAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="password")
        if hasattr(self.owner, "role"):
            self.owner.role = "vendor"
            self.owner.save()
            
        self.shop = Shop.objects.create(owner=self.owner, name="Owner Shop", status=Shop.ShopStatus.APPROVED)
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(shop=self.shop, category=self.category, name="Test Product", status=Product.ProductStatus.ACTIVE)
        self.variant = ProductVariant.objects.create(product=self.product, sku="TEST-SKU", price=15.0)
        self.inventory = Inventory.objects.create(variant=self.variant, quantity_on_hand=100)

        self.transactions_url = reverse("inventory-transactions", kwargs={"shop_slug": self.shop.slug, "product_slug": self.product.slug, "sku": self.variant.sku})
        
        self.client.force_authenticate(user=self.owner)

    def test_increase_stock(self):
        payload = {"action": "increase", "quantity": 50, "note": "Restock"}
        response = self.client.post(self.transactions_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_on_hand, 150)
        
        transaction = InventoryTransaction.objects.last()
        self.assertEqual(transaction.transaction_type, InventoryTransaction.TransactionType.IN)
        self.assertEqual(transaction.quantity, 50)

    def test_decrease_stock(self):
        payload = {"action": "decrease", "quantity": 20, "note": "Damage"}
        response = self.client.post(self.transactions_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_on_hand, 80)
        
        transaction = InventoryTransaction.objects.last()
        self.assertEqual(transaction.transaction_type, InventoryTransaction.TransactionType.OUT)
        self.assertEqual(transaction.quantity, 20)

    def test_decrease_below_zero_fails(self):
        payload = {"action": "decrease", "quantity": 200, "note": "Too much damage"}
        response = self.client.post(self.transactions_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_on_hand, 100)

    def test_adjust_stock_increase(self):
        payload = {"action": "adjust", "quantity": 120, "note": "Manual count"}
        response = self.client.post(self.transactions_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_on_hand, 120)
        
        transaction = InventoryTransaction.objects.last()
        self.assertEqual(transaction.transaction_type, InventoryTransaction.TransactionType.ADJUST)
        self.assertEqual(transaction.quantity, 20)
        
    def test_adjust_stock_decrease(self):
        payload = {"action": "adjust", "quantity": 90, "note": "Manual count"}
        response = self.client.post(self.transactions_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_on_hand, 90)
        
        transaction = InventoryTransaction.objects.last()
        self.assertEqual(transaction.transaction_type, InventoryTransaction.TransactionType.ADJUST)
        self.assertEqual(transaction.quantity, 10)

    def test_transaction_history_list(self):
        # Create some transactions
        self.client.post(self.transactions_url, {"action": "increase", "quantity": 10})
        self.client.post(self.transactions_url, {"action": "decrease", "quantity": 5})
        
        response = self.client.get(self.transactions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(isinstance(data, list) or "results" in data)
        results = data if isinstance(data, list) else data["results"]
        
        self.assertEqual(len(results), 2)
        # Verify ordering (latest first)
        self.assertEqual(results[0]["transaction_type"], "OUT")
        self.assertEqual(results[1]["transaction_type"], "IN")
