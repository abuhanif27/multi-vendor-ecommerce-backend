from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from datetime import date
from decimal import Decimal

from apps.shops.models import Shop, Product, Category
from apps.analytics.models import ShopMetricRollup, ProductVelocityRollup, MetricPeriod

User = get_user_model()

class AnalyticsAPITestCase(APITestCase):
    def setUp(self):
        self.vendor = User.objects.create_user(email="vendor@example.com", password="pwd")
        self.shop = Shop.objects.create(owner=self.vendor, name="Vendor Shop")
        
        self.admin = User.objects.create_superuser(email="admin@example.com", password="pwd")
        self.other_shop = Shop.objects.create(owner=self.admin, name="Other Shop") # Just another shop
        
        self.today = date.today()
        
        ShopMetricRollup.objects.create(
            shop=self.shop,
            period=MetricPeriod.DAILY,
            period_start=self.today,
            period_end=self.today,
            gross_revenue=Decimal('100.00'),
            net_revenue=Decimal('90.00'),
            order_count=2,
            cancellation_count=0,
            return_count=0
        )
        
        self.category = Category.objects.create(name="Tech")
        self.product = Product.objects.create(shop=self.shop, category=self.category, name="Laptop")
        
        ProductVelocityRollup.objects.create(
            shop=self.shop,
            product=self.product,
            period=MetricPeriod.ALL_TIME,
            period_start=None,
            period_end=None,
            units_sold=5,
            gross_revenue=Decimal('500.00')
        )
        
    def test_vendor_dashboard_success(self):
        self.client.force_authenticate(user=self.vendor)
        url = reverse('analytics-dashboard')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(float(data['sales_summary']['gross_revenue']), 100.0)
        self.assertEqual(data['sales_summary']['order_count'], 2)
        self.assertEqual(float(data['sales_summary']['average_order_value']), 50.0)
        
        self.assertEqual(len(data['widgets']), 2)
        self.assertEqual(data['widgets'][0]['title'], "Gross Revenue")
        
        self.assertEqual(len(data['top_products']), 1)
        self.assertEqual(data['top_products'][0]['product_name'], "Laptop")
        
    def test_invalid_date_range(self):
        self.client.force_authenticate(user=self.vendor)
        url = reverse('analytics-dashboard')
        
        response = self.client.get(f"{url}?start_date=2023-12-31&end_date=2023-01-01")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start_date cannot be after end_date", response.json()['detail'])

    def test_unauthorized_access(self):
        url = reverse('analytics-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_buyer_without_shop_forbidden(self):
        buyer = User.objects.create_user(email="buyer@example.com", password="pwd")
        self.client.force_authenticate(user=buyer)
        
        url = reverse('analytics-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_admin_can_view_any_shop(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('analytics-dashboard')
        response = self.client.get(f"{url}?shop_id={self.shop.id}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.json()['sales_summary']['gross_revenue']), 100.0)

    def test_export_sales_endpoint(self):
        self.client.force_authenticate(user=self.vendor)
        url = reverse('analytics-export-sales')
        
        response = self.client.post(f"{url}?start_date=2023-01-01&end_date=2023-12-31")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("Export triggered successfully", response.json()['detail'])
