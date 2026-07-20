from typing import Optional
from datetime import date
import csv
import io

from apps.analytics.models import ShopMetricRollup

class ReportingService:
    """
    Handles expensive export generation operations.
    Designed to be invoked via Celery tasks.
    """
    
    @staticmethod
    def generate_sales_csv(shop_id: Optional[str], start_date: date, end_date: date) -> str:
        """
        Generates a CSV string containing daily sales metrics.
        """
        qs = ShopMetricRollup.objects.filter(
            shop_id=shop_id,
            period='DAILY',
            period_start__gte=start_date,
            period_end__lte=end_date
        ).order_by('period_start')
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write Headers
        writer.writerow(['Date', 'Gross Revenue', 'Net Revenue', 'Orders', 'Cancellations', 'Returns'])
        
        # Write Rows
        for row in qs:
            writer.writerow([
                row.period_start.isoformat(),
                str(row.gross_revenue),
                str(row.net_revenue),
                str(row.order_count),
                str(row.cancellation_count),
                str(row.return_count)
            ])
            
        return output.getvalue()
