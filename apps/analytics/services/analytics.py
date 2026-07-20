from decimal import Decimal
from typing import List, Optional
from datetime import date
from django.db.models import Sum

from apps.analytics.models import ShopMetricRollup, ProductVelocityRollup, MetricPeriod
from apps.analytics.dtos import SalesSummaryDTO, TopProductDTO, WidgetDataDTO

class AnalyticsService:
    """
    Calculates derived KPIs purely from raw rollup facts.
    """
    
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
