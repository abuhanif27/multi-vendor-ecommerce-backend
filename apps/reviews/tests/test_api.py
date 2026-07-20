from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.shops.models import Shop, Product, Category, ProductVariant
from apps.orders.models import Order, VendorOrder, OrderItem
from apps.reviews.models import ProductReview, ReviewStatus

User = get_user_model()

class ReviewAPITestCase(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(email="buyer@example.com", password="password")
        self.other_buyer = User.objects.create_user(email="other@example.com", password="password")
        self.vendor = User.objects.create_user(email="vendor@example.com", password="password")
        self.admin = User.objects.create_superuser(email="admin@example.com", password="password")
        
        self.shop = Shop.objects.create(owner=self.vendor, name="Test Shop")
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(shop=self.shop, category=self.category, name="Laptop")
        self.variant = ProductVariant.objects.create(product=self.product, sku="LAP-1", price=1000)
        
        self.order = Order.objects.create(
            user=self.buyer,
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
        
        self.list_create_url = reverse('product-review-list')

    def test_verified_purchaser_can_create_review(self):
        self.client.force_authenticate(user=self.buyer)
        data = {
            "product_id": str(self.product.id),
            "order_item_id": str(self.order_item.id),
            "rating": 5,
            "comment": "Excellent!"
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductReview.objects.count(), 1)
        
    def test_non_purchaser_cannot_create_review(self):
        self.client.force_authenticate(user=self.other_buyer)
        data = {
            "product_id": str(self.product.id),
            "order_item_id": str(self.order_item.id),
            "rating": 5
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You can only review items you purchased.", response.data['detail'])

    def test_duplicate_review_rejection(self):
        self.client.force_authenticate(user=self.buyer)
        data = {
            "product_id": str(self.product.id),
            "order_item_id": str(self.order_item.id),
            "rating": 5
        }
        self.client.post(self.list_create_url, data)
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You have already reviewed this item.", response.data['detail'])

    def test_update_review(self):
        self.client.force_authenticate(user=self.buyer)
        data = {
            "product_id": str(self.product.id),
            "order_item_id": str(self.order_item.id),
            "rating": 5
        }
        response = self.client.post(self.list_create_url, data)
        review_id = response.data['id']
        
        url = reverse('product-review-detail', args=[review_id])
        update_data = {"rating": 3, "comment": "Changed my mind"}
        response2 = self.client.patch(url, update_data)
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['rating'], 3)
        self.assertEqual(response2.data['comment'], "Changed my mind")
        self.assertTrue(response2.data['is_edited'])

    def test_delete_review(self):
        self.client.force_authenticate(user=self.buyer)
        data = {
            "product_id": str(self.product.id),
            "order_item_id": str(self.order_item.id),
            "rating": 5
        }
        res = self.client.post(self.list_create_url, data)
        review_id = res.data['id']
        
        url = reverse('product-review-detail', args=[review_id])
        del_res = self.client.delete(url)
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ProductReview.objects.count(), 0)

    def test_list_reviews_and_filtering(self):
        # Create review 1
        ProductReview.objects.create(
            user=self.buyer,
            product=self.product,
            order_item=self.order_item,
            rating=5,
            comment="Awesome",
            status=ReviewStatus.PUBLISHED
        )
        
        # Create second purchase and review
        order2 = Order.objects.create(user=self.other_buyer, status=Order.OrderStatus.COMPLETED, shipping_address={}, subtotal=0, grand_total=0)
        vo2 = VendorOrder.objects.create(order=order2, shop=self.shop, status=VendorOrder.FulfillmentStatus.DELIVERED)
        item2 = OrderItem.objects.create(vendor_order=vo2, variant=self.variant, product_name="x", sku="y", unit_price=1, quantity=1, item_total=1)
        ProductReview.objects.create(
            user=self.other_buyer,
            product=self.product,
            order_item=item2,
            rating=2,
            comment="Bad",
            status=ReviewStatus.PUBLISHED
        )
        
        # List all
        res = self.client.get(self.list_create_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 2)
        
        # Filter by rating
        res_filter = self.client.get(self.list_create_url + '?rating=5')
        self.assertEqual(len(res_filter.data['results']), 1)
        self.assertEqual(res_filter.data['results'][0]['rating'], 5)

    def test_vendor_can_read_not_write(self):
        ProductReview.objects.create(
            user=self.buyer,
            product=self.product,
            order_item=self.order_item,
            rating=5,
            status=ReviewStatus.PUBLISHED
        )
        self.client.force_authenticate(user=self.vendor)
        res = self.client.get(self.list_create_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)
        
        review_id = res.data['results'][0]['id']
        url = reverse('product-review-detail', args=[review_id])
        
        # Vendor cannot update
        update_res = self.client.patch(url, {"rating": 1})
        self.assertEqual(update_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_report_abuse(self):
        ProductReview.objects.create(
            user=self.buyer,
            product=self.product,
            order_item=self.order_item,
            rating=5,
            status=ReviewStatus.PUBLISHED
        )
        # Fetch list to get ID
        res = self.client.get(self.list_create_url)
        review_id = res.data['results'][0]['id']
        
        url = reverse('product-review-report', args=[review_id])
        
        self.client.force_authenticate(user=self.other_buyer)
        report_res = self.client.post(url, {"reason": "Spam content"})
        self.assertEqual(report_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(report_res.data['reason'], "Spam content")
        self.assertEqual(str(report_res.data['review']), str(review_id))
