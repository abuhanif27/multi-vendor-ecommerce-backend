from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from unittest.mock import patch

from apps.shops.models import Shop
from apps.analytics.models import ShopMetricRollup, MetricPeriod
from apps.analytics.services.analytics import AnalyticsService
from apps.analytics.services.reporting import ReportingService
from apps.analytics.events import handle_order_completed_event

User = get_user_model()

class MockEvent:
    def __init__(self, shop_id, gross_total, net_total, discount_total):
        self.shop_id = shop_id
        self.gross_total = gross_total
        self.net_total = net_total
        self.discount_total = discount_total

class AnalyticsServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="vendor@test.com", password="pwd")
        self.shop = Shop.objects.create(owner=self.user, name="Test Shop")
        
        self.today = date(2023, 10, 15)
        
    @patch('apps.analytics.events.timezone.now')
    def test_update_shop_metric_event(self, mock_now):
        # Mock timezone.now()
        from datetime import datetime, timezone
        mock_now.return_value = datetime(2023, 10, 15, tzinfo=timezone.utc)
        
        event = MockEvent(self.shop.id, Decimal('100.00'), Decimal('90.00'), Decimal('10.00'))
        handle_order_completed_event(event)
        
        # Verify DAILY rollup created
        daily = ShopMetricRollup.objects.get(shop=self.shop, period=MetricPeriod.DAILY, period_start=self.today)
        self.assertEqual(daily.gross_revenue, Decimal('100.00'))
        self.assertEqual(daily.order_count, 1)
        
        # Fire a second mock event (zero discount)
        event2 = MockEvent(self.shop.id, Decimal('50.00'), Decimal('50.00'), Decimal('0.00'))
        handle_order_completed_event(event2)
        
        # Verify DAILY rollup accumulated atomically
        daily.refresh_from_db()
        self.assertEqual(daily.gross_revenue, Decimal('150.00'))
        self.assertEqual(daily.order_count, 2)
        
        # Verify MONTHLY rollup created
        monthly = ShopMetricRollup.objects.get(shop=self.shop, period=MetricPeriod.MONTHLY)
        self.assertEqual(monthly.period_start, date(2023, 10, 1))
        self.assertEqual(monthly.gross_revenue, Decimal('150.00'))
        
        # Verify MARKETPLACE rollup created
        marketplace_daily = ShopMetricRollup.objects.get(shop__isnull=True, period=MetricPeriod.DAILY, period_start=self.today)
        self.assertEqual(marketplace_daily.gross_revenue, Decimal('150.00'))
        self.assertEqual(marketplace_daily.order_count, 2)
        
    def test_analytics_service_derived_kpis(self):
        # Create mock data
        ShopMetricRollup.objects.create(
            shop=self.shop,
            period=MetricPeriod.DAILY,
            period_start=self.today,
            period_end=self.today,
            gross_revenue=Decimal('150.00'),
            net_revenue=Decimal('140.00'),
            order_count=2,
            cancellation_count=0,
            return_count=1 # 50% return rate
        )
        
        # Compute KPIs
        summary = AnalyticsService.get_sales_summary(
            shop_id=self.shop.id,
            period='DAILY',
            period_start=self.today,
            period_end=self.today
        )
        
        self.assertEqual(summary.gross_revenue, Decimal('150.00'))
        self.assertEqual(summary.order_count, 2)
        self.assertEqual(summary.average_order_value, Decimal('75.00'))
        self.assertEqual(summary.return_rate, Decimal('50.00'))
        self.assertEqual(summary.cancellation_rate, Decimal('0.00'))
        
    def test_zero_value_edge_case(self):
        # Create mock data with 0 orders
        ShopMetricRollup.objects.create(
            shop=self.shop,
            period=MetricPeriod.DAILY,
            period_start=self.today,
            period_end=self.today,
            gross_revenue=Decimal('0.00'),
            net_revenue=Decimal('0.00'),
            order_count=0,
            cancellation_count=0,
            return_count=0
        )
        
        summary = AnalyticsService.get_sales_summary(
            shop_id=self.shop.id,
            period='DAILY',
            period_start=self.today,
            period_end=self.today
        )
        self.assertEqual(summary.average_order_value, Decimal('0.00'))
        self.assertEqual(summary.return_rate, Decimal('0.00'))
        
    def test_reporting_service_csv(self):
        ShopMetricRollup.objects.create(
            shop=self.shop,
            period=MetricPeriod.DAILY,
            period_start=self.today,
            period_end=self.today,
            gross_revenue=Decimal('100.00'),
            net_revenue=Decimal('90.00'),
            order_count=1
        )
        
        csv_out = ReportingService.generate_sales_csv(
            shop_id=self.shop.id,
            start_date=self.today,
            end_date=self.today
        )
        
        self.assertIn("Date,Gross Revenue,Net Revenue,Orders,Cancellations,Returns", csv_out)
        self.assertIn("2023-10-15,100.00,90.00,1", csv_out)
