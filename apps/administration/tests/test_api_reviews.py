import uuid
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITransactionTestCase
from rest_framework import status
from apps.shops.models import Shop, Product
from apps.catalog.models import Category
from apps.orders.models import Order, OrderItem, VendorOrder
from apps.reviews.models import ProductReview, ShopReview, ReviewStatus, ProductReviewReport, ShopReviewReport
from apps.notifications.events import EventBus
from apps.administration.events import ProductReviewModeratedEvent, ShopReviewModeratedEvent
from apps.administration.models import AdminAuditLog
from django.contrib.auth.models import Permission

User = get_user_model()

class ReviewModerationAPITests(APITransactionTestCase):
    def setUp(self):
        EventBus.clear()
        
        self.super_admin = User.objects.create_superuser(email="admin@example.com", password="password")
        self.vendor_user = User.objects.create_user(email="vendor@example.com", password="password")
        self.buyer_user = User.objects.create_user(email="buyer@example.com", password="password")
        self.staff_no_perms = User.objects.create_user(email="staff@example.com", password="password", is_staff=True)
        
        # Give super_admin the can_moderate_reviews perm just to be safe, though superusers usually bypass this.
        # But we'll test with a specific admin user that has the perm.
        self.admin_user = User.objects.create_user(email="mod@example.com", password="password", is_staff=True)
        perm = Permission.objects.get(codename='can_moderate_reviews')
        self.admin_user.user_permissions.add(perm)

        # Setup Shop, Product, Order
        self.shop = Shop.objects.create(name="Test Shop", owner=self.vendor_user, status=Shop.ShopStatus.APPROVED)
        self.category = Category.objects.create(name="Test Category", slug="test-category")
        self.product = Product.objects.create(
            name="Test Product", shop=self.shop, category=self.category, status=Product.ProductStatus.ACTIVE
        )
        
        self.order = Order.objects.create(user=self.buyer_user, shipping_address={}, billing_address={})
        self.vendor_order = VendorOrder.objects.create(order=self.order, shop=self.shop, status=VendorOrder.FulfillmentStatus.DELIVERED)
        self.order_item = OrderItem.objects.create(
            vendor_order=self.vendor_order, product_name=self.product.name, quantity=1, unit_price=10.0, item_total=10.0
        )
        # Assuming order_item needs a variant in real models, we mock it or set appropriately.
        # However, we can just create the ProductReview bypassing the service constraints for test setup.
        
        self.product_review = ProductReview.objects.create(
            user=self.buyer_user,
            product=self.product,
            order_item=self.order_item,
            rating=5,
            comment="Great product",
            status=ReviewStatus.PUBLISHED
        )

        self.shop_review = ShopReview.objects.create(
            user=self.buyer_user,
            shop=self.shop,
            vendor_order=self.vendor_order,
            rating=5,
            comment="Great shop",
            status=ReviewStatus.PUBLISHED
        )

        self.events_published = []
        def mock_handler(event):
            self.events_published.append(event)
            
        EventBus.subscribe(ProductReviewModeratedEvent, mock_handler)
        EventBus.subscribe(ShopReviewModeratedEvent, mock_handler)

    def test_anonymous_and_no_perms_blocked(self):
        url = reverse('admin-product-review-hide', kwargs={'review_id': self.product_review.id})
        resp = self.client.post(url, {"reason": "bad word"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        
        self.client.force_authenticate(user=self.staff_no_perms)
        resp = self.client.post(url, {"reason": "bad word"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_hide_product_review(self):
        self.client.force_authenticate(user=self.admin_user)
        
        # Create a report to verify resolution
        report = ProductReviewReport.objects.create(reporter=self.vendor_user, review=self.product_review, reason="spam")
        
        url = reverse('admin-product-review-hide', kwargs={'review_id': self.product_review.id})
        resp = self.client.post(url, {"reason": "Investigating"})
        
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.product_review.refresh_from_db()
        self.assertEqual(self.product_review.status, ReviewStatus.HIDDEN)
        
        # Verify reports are resolved
        report.refresh_from_db()
        self.assertTrue(report.is_resolved)
        
        # Verify events
        self.assertEqual(len(self.events_published), 1)
        event = self.events_published[0]
        self.assertIsInstance(event, ProductReviewModeratedEvent)
        self.assertEqual(event.new_status, ReviewStatus.HIDDEN)
        
        # Verify Audit Log
        audit = AdminAuditLog.objects.last()
        self.assertEqual(audit.action, "UPDATE")
        self.assertEqual(audit.resource_type, "ProductReview")

    def test_remove_shop_review(self):
        self.client.force_authenticate(user=self.admin_user)
        
        report = ShopReviewReport.objects.create(reporter=self.vendor_user, review=self.shop_review, reason="spam")
        
        url = reverse('admin-shop-review-remove', kwargs={'review_id': self.shop_review.id})
        resp = self.client.post(url, {"reason": "Violates guidelines"})
        
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.shop_review.refresh_from_db()
        self.assertEqual(self.shop_review.status, ReviewStatus.REMOVED)
        
        report.refresh_from_db()
        self.assertTrue(report.is_resolved)
        
        self.assertEqual(len(self.events_published), 1)
        self.assertIsInstance(self.events_published[0], ShopReviewModeratedEvent)
        self.assertEqual(self.events_published[0].new_status, ReviewStatus.REMOVED)

    def test_restore_product_review(self):
        self.product_review.status = ReviewStatus.HIDDEN
        self.product_review.save()
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('admin-product-review-restore', kwargs={'review_id': self.product_review.id})
        resp = self.client.post(url)
        
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.product_review.refresh_from_db()
        self.assertEqual(self.product_review.status, ReviewStatus.PUBLISHED)
