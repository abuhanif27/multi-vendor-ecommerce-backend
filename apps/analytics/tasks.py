from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from apps.analytics.models import ShopMetricRollup, MetricPeriod
# from apps.orders.models import Order # Assuming Order model exists

@shared_task
def reconcile_daily_metrics():
    """
    Runs nightly at 2 AM. 
    Recalculates the previous day's metrics from the source of truth (Order tables)
    and forcibly overwrites the ShopMetricRollup to heal any desync from missed events.
    """
    yesterday = timezone.now().date() - timedelta(days=1)
    
    # 1. Fetch total orders grouped by shop from the actual orders table.
    # pseudo-code:
    # qs = Order.objects.filter(created_at__date=yesterday).values('shop_id').annotate(
    #     total_gross=Sum('gross_total'),
    #     total_net=Sum('net_total'),
    #     count=Count('id')
    # )
    
    # 2. Iterate through results and overwrite the DAILY rollup row:
    # with transaction.atomic():
    #     for row in qs:
    #         ShopMetricRollup.objects.update_or_create(
    #             shop_id=row['shop_id'],
    #             period=MetricPeriod.DAILY,
    #             period_start=yesterday,
    #             period_end=yesterday,
    #             defaults={
    #                 'gross_revenue': row['total_gross'],
    #                 'net_revenue': row['total_net'],
    #                 'order_count': row['count']
    #             }
    #         )
    pass

@shared_task
def generate_vendor_sales_report(shop_id, start_date_str, end_date_str, user_email):
    """
    Background job triggered by an API request.
    Generates CSV via ReportingService and sends via email.
    """
    from apps.analytics.services.reporting import ReportingService
    from datetime import datetime
    
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    
    csv_data = ReportingService.generate_sales_csv(shop_id, start_date, end_date)
    
    # email_service.send_email(
    #    to=user_email, 
    #    subject="Your Sales Report", 
    #    attachment=csv_data
    # )
    pass
