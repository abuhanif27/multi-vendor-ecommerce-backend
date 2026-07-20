from decimal import Decimal
from typing import List, Optional
from datetime import date, timedelta
from django.db.models import Sum, F
from django.db import IntegrityError
from django.core.cache import cache

from apps.analytics.models import ShopMetricRollup, ProductVelocityRollup, MetricPeriod
from apps.analytics.dtos import SalesSummaryDTO, TopProductDTO, WidgetDataDTO

class AnalyticsService:
    """
    Calculates derived KPIs purely from raw rollup facts and handles metrics updates.
    """
    
    @staticmethod
    def get_cache_version(shop_id: Optional[str]) -> int:
        key = f"analytics_version_{shop_id or 'marketplace'}"
        return cache.get_or_set(key, 1, timeout=None)

    @staticmethod
    def bump_cache_version(shop_id: Optional[str]):
        key = f"analytics_version_{shop_id or 'marketplace'}"
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=None)

    @staticmethod
    def get_period_boundaries(date_obj: date, period: str):
        if period == MetricPeriod.DAILY:
            return date_obj, date_obj
        if period == MetricPeriod.MONTHLY:
            start = date_obj.replace(day=1)
            if start.month == 12:
                end = start.replace(year=start.year+1, month=1, day=1) - timedelta(days=1)
            else:
                end = start.replace(month=start.month+1, day=1) - timedelta(days=1)
            return start, end
        if period == MetricPeriod.ALL_TIME:
            return None, None
        return date_obj, date_obj

    @staticmethod
    def increment_shop_metrics(shop_id: Optional[str], event_date: date, gross: Decimal, net: Decimal, discount: Decimal, is_new_order: bool = True):
        periods = [MetricPeriod.DAILY, MetricPeriod.MONTHLY, MetricPeriod.ALL_TIME]
        
        for period in periods:
            start, end = AnalyticsService.get_period_boundaries(event_date, period)
            
            # Atomic lock-free increment
            updated = ShopMetricRollup.objects.filter(
                shop_id=shop_id, period=period, period_start=start, period_end=end
            ).update(
                gross_revenue=F('gross_revenue') + gross,
                net_revenue=F('net_revenue') + net,
                total_discount_amount=F('total_discount_amount') + discount,
                order_count=F('order_count') + (1 if is_new_order else 0)
            )
            
            if not updated:
                try:
                    ShopMetricRollup.objects.create(
                        shop_id=shop_id, period=period, period_start=start, period_end=end,
                        gross_revenue=gross, net_revenue=net, total_discount_amount=discount,
                        order_count=(1 if is_new_order else 0)
                    )
                except IntegrityError:
                    # Race condition caught
                    ShopMetricRollup.objects.filter(
                        shop_id=shop_id, period=period, period_start=start, period_end=end
                    ).update(
                        gross_revenue=F('gross_revenue') + gross,
                        net_revenue=F('net_revenue') + net,
                        total_discount_amount=F('total_discount_amount') + discount,
                        order_count=F('order_count') + (1 if is_new_order else 0)
                    )
        
        # Bump the cache version string for this shop to invalidate dashboard fragments
        AnalyticsService.bump_cache_version(shop_id)

    @staticmethod
    def get_sales_summary(shop_id: Optional[str], period: str, period_start: date, period_end: date) -> SalesSummaryDTO:
        """
        Fetches the rollup table row for the given period boundaries and computes derived KPIs (AOV, Rates).
        If multiple rows exist for a custom range, it aggregates them on the fly.
        """
        # If it's a standard period, we should just query the exact rollup
        qs = ShopMetricRollup.objects.filter(
            shop_id=shop_id, 
            period_start__gte=period_start,
            period_end__lte=period_end
        )
        
        agg = qs.aggregate(
            gross=Sum('gross_revenue'),
            net=Sum('net_revenue'),
            orders=Sum('order_count'),
            cancels=Sum('cancellation_count'),
            returns=Sum('return_count')
        )
        
        gross = agg['gross'] or Decimal('0.00')
        net = agg['net'] or Decimal('0.00')
        orders = agg['orders'] or 0
        cancels = agg['cancels'] or 0
        returns = agg['returns'] or 0
        
        aov = (gross / orders) if orders > 0 else Decimal('0.00')
        cancellation_rate = (Decimal(cancels) / Decimal(orders) * 100) if orders > 0 else Decimal('0.00')
        return_rate = (Decimal(returns) / Decimal(orders) * 100) if orders > 0 else Decimal('0.00')
        
        return SalesSummaryDTO(
            gross_revenue=gross,
            net_revenue=net,
            order_count=orders,
            average_order_value=aov.quantize(Decimal('0.01')),
            cancellation_rate=cancellation_rate.quantize(Decimal('0.01')),
            return_rate=return_rate.quantize(Decimal('0.01'))
        )

    @staticmethod
    def get_top_products(shop_id: Optional[str], limit: int = 10) -> List[TopProductDTO]:
        """
        Queries the ALL_TIME product velocity rollups and sorts by units_sold.
        """
        qs = ProductVelocityRollup.objects.filter(
            shop_id=shop_id, 
            period=MetricPeriod.ALL_TIME
        ).order_by('-units_sold', '-gross_revenue')[:limit]
        
        return [
            TopProductDTO(
                product_id=str(row.product_id),
                product_name=row.product.name,
                units_sold=row.units_sold,
                gross_revenue=row.gross_revenue
            ) for row in qs
        ]
