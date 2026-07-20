from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from apps.shops.models import Shop, Product, ProductVariant, Category
from apps.inventory.models import Inventory
from apps.cart.services.cart import CartService
from apps.cart.models import CartItem
from decimal import Decimal
import threading

User = get_user_model()

class CartServiceConcurrencyTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="buyer@test.com", password="pwd")
        self.vendor = User.objects.create_user(email="vendor@test.com", password="pwd")
        self.shop = Shop.objects.create(owner=self.vendor, name="Vendor Shop")
        self.category = Category.objects.create(name="Tech")
        self.product = Product.objects.create(shop=self.shop, category=self.category, name="Laptop")
        self.variant = ProductVariant.objects.create(
            product=self.product, 
            sku="LAPTOP-1", 
            price=Decimal('1000.00'),
            status=ProductVariant.VariantStatus.ACTIVE
        )
        self.product.status = 'active'
        self.product.save()
        self.inventory = Inventory.objects.create(variant=self.variant, quantity_on_hand=100)

    def test_concurrent_add_item(self):
        from django.db import connection
        if connection.vendor == 'sqlite':
            self.skipTest("SQLite does not support concurrent select_for_update well.")
            
        def add_to_cart():
            # We must use a separate connection/transaction per thread, TransactionTestCase handles this
            # if we use atomic inside the thread, but we must make sure database connections are closed/handled
            from django.db import connection
            try:
                CartService.add_item(self.user, "LAPTOP-1", 1)
            finally:
                connection.close()

        threads = []
        for _ in range(5):
            t = threading.Thread(target=add_to_cart)
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        # If concurrency is safe, the item should exist exactly once with quantity 5
        items = CartItem.objects.filter(cart__user=self.user)
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().quantity, 5)
