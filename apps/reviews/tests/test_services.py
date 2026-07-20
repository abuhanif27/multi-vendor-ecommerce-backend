from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.shops.models import Shop, Product, Category
from apps.orders.models import Order, VendorOrder, OrderItem
from apps.catalog.models import CategoryAttribute, CategoryAttributeValue
from apps.inventory.models import Inventory
from apps.shops.models import ProductVariant

from apps.reviews.services.review import ReviewService
from apps.reviews.models import ProductReview, ShopReview, ReviewStatus
from apps.notifications.events import EventBus

User = get_user_model()

class ReviewServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="buyer@example.com", password="password")
        self.other_user = User.objects.create_user(email="other@example.com", password="password")
        self.vendor = User.objects.create_user(email="vendor@example.com", password="password")
        
        self.shop = Shop.objects.create(owner=self.vendor, name="Test Shop")
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(shop=self.shop, category=self.category, name="Laptop")
        self.variant = ProductVariant.objects.create(product=self.product, sku="LAP-1", price=1000)
        
        self.order = Order.objects.create(
            user=self.user,
            subtotal=1000,
            grand_total=1000,
            status=Order.OrderStatus.COMPLETED,
            shipping_address={}
        )
        
        self.vendor_order = VendorOrder.objects.create(
            order=self.order,
            shop=self.shop,
            status=VendorOrder.FulfillmentStatus.DELIVERED
        )
        
        self.order_item = OrderItem.objects.create(
            vendor_order=self.vendor_order,
            variant=self.variant,
            product_name=self.product.name,
            sku=self.variant.sku,
            unit_price=1000,
            quantity=1,
            item_total=1000
        )
        
        EventBus.clear()

    def test_verified_purchase_successful(self):
        """Test a buyer can review a product they bought after it is completed."""
        review = ReviewService.create_product_review(
            user=self.user,
            product_id=self.product.id,
            order_item_id=self.order_item.id,
            rating=5,
            comment="Great!"
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.status, ReviewStatus.PUBLISHED)
        
    def test_cannot_review_others_purchase(self):
        """Test a buyer cannot review an order item belonging to someone else."""
        with self.assertRaisesMessage(ValidationError, "You can only review items you purchased."):
            ReviewService.create_product_review(
                user=self.other_user,
                product_id=self.product.id,
                order_item_id=self.order_item.id,
                rating=5
            )
            
    def test_cannot_review_uncompleted_order(self):
        """Test a buyer cannot review an item before it is completed (delivered)."""
        self.vendor_order.status = VendorOrder.FulfillmentStatus.PENDING
        self.vendor_order.save()
        
        with self.assertRaisesMessage(ValidationError, "You can only review items after the order is completed."):
            ReviewService.create_product_review(
                user=self.user,
                product_id=self.product.id,
                order_item_id=self.order_item.id,
                rating=5
            )
            
    def test_cannot_review_wrong_product(self):
        """Test the order item must logically match the product ID."""
        other_product = Product.objects.create(shop=self.shop, category=self.category, name="Mouse")
        
        with self.assertRaisesMessage(ValidationError, "Order item does not match the product being reviewed."):
            ReviewService.create_product_review(
                user=self.user,
                product_id=other_product.id,
                order_item_id=self.order_item.id,
                rating=5
            )
            
    def test_duplicate_review_blocked(self):
        """Test only one review per order item."""
        ReviewService.create_product_review(
            user=self.user,
            product_id=self.product.id,
            order_item_id=self.order_item.id,
            rating=5
        )
        
        with self.assertRaisesMessage(ValidationError, "You have already reviewed this item."):
            ReviewService.create_product_review(
                user=self.user,
                product_id=self.product.id,
                order_item_id=self.order_item.id,
                rating=4
            )
            
    def test_sync_product_rating(self):
        """Test that the denormalized metrics are mathematically correct."""
        ReviewService.create_product_review(
            user=self.user,
            product_id=self.product.id,
            order_item_id=self.order_item.id,
            rating=4
        )
        
        # Fake a second purchase by another user
        order2 = Order.objects.create(user=self.other_user, status=Order.OrderStatus.COMPLETED, shipping_address={}, grand_total=1, subtotal=1)
        vo2 = VendorOrder.objects.create(order=order2, shop=self.shop, status=VendorOrder.FulfillmentStatus.DELIVERED)
        item2 = OrderItem.objects.create(vendor_order=vo2, variant=self.variant, product_name="L", sku="L", unit_price=1, quantity=1, item_total=1)
        
        ReviewService.create_product_review(
            user=self.other_user,
            product_id=self.product.id,
            order_item_id=item2.id,
            rating=5
        )
        
        # Trigger the sync
        ReviewService.sync_product_rating(self.product.id)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.review_count, 2)
        self.assertEqual(self.product.average_rating, 4.50)
