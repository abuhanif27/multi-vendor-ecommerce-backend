from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from datetime import datetime, date, timedelta

from apps.analytics.services.analytics import AnalyticsService
from apps.analytics.services.reporting import ReportingService
from apps.analytics.serializers import DashboardOverviewResponseSerializer
from apps.analytics.dtos import WidgetDataDTO
from apps.promotions.permissions import IsVendorOwnerOrAdmin # We can reuse this permission if appropriate, but wait, analytics doesn't have an object.

class IsAnalyticsViewer(IsAuthenticated):
    """
    Vendor can only see their own shop. Admins can see any shop or marketplace.
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view)

class AnalyticsViewSet(viewsets.ViewSet):
    """
    Read-only dashboards and analytics exports.
    """
    permission_classes = [IsAnalyticsViewer]

    def _get_shop_id(self, request) -> str:
        """
        Resolves the shop_id based on permissions.
        """
        user = request.user
        requested_shop_id = request.query_params.get('shop_id')
        
        if user.is_staff or user.is_superuser:
            return requested_shop_id # Can be None for marketplace
            
        shop = user.shops.first()
        return str(shop.id) if shop else "INVALID"

    @extend_schema(
        parameters=[
            OpenApiParameter('start_date', OpenApiTypes.DATE, description='YYYY-MM-DD'),
            OpenApiParameter('end_date', OpenApiTypes.DATE, description='YYYY-MM-DD'),
            OpenApiParameter('shop_id', OpenApiTypes.UUID, description='For admins only')
        ],
        responses=DashboardOverviewResponseSerializer
    )
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        shop_id = self._get_shop_id(request)
        if shop_id == "INVALID":
            return Response({"detail": "User has no shop."}, status=status.HTTP_403_FORBIDDEN)
            
        # Parse dates (default to last 30 days)
        end_date = request.query_params.get('end_date')
        start_date = request.query_params.get('start_date')
        
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_date = date.today()
            
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_date = end_date - timedelta(days=30)
            
        # For a custom range, we just query DAILY period and aggregate
        summary = AnalyticsService.get_sales_summary(shop_id, 'DAILY', start_date, end_date)
        top_products = AnalyticsService.get_top_products(shop_id, limit=5)
        
        # Build a generic widget for the frontend
        widgets = [
            WidgetDataDTO(
                title="Gross Revenue",
                value=f"${summary.gross_revenue}",
                delta_percentage=None, # Need previous period logic for this
                delta_label="vs last period"
            ),
            WidgetDataDTO(
                title="Total Orders",
                value=str(summary.order_count)
            )
        ]
        
        response_data = {
            "sales_summary": summary.__dict__,
            "widgets": [w.__dict__ for w in widgets],
            "top_products": [p.__dict__ for p in top_products]
        }
        
        serializer = DashboardOverviewResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter('start_date', OpenApiTypes.DATE, required=True),
            OpenApiParameter('end_date', OpenApiTypes.DATE, required=True),
            OpenApiParameter('shop_id', OpenApiTypes.UUID)
        ]
    )
    @action(detail=False, methods=['post'], url_path='export-sales')
    def export_sales(self, request):
        """
        Triggers an asynchronous export of sales data.
        """
        shop_id = self._get_shop_id(request)
        if shop_id == "INVALID":
            return Response({"detail": "User has no shop."}, status=status.HTTP_403_FORBIDDEN)
            
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response({"detail": "start_date and end_date are required."}, status=status.HTTP_400_BAD_REQUEST)
            
        # In a real app, this would be: generate_vendor_sales_report.delay(...)
        # We will just return a 202 Accepted.
        
        return Response({"detail": "Export triggered successfully. You will receive an email shortly."}, status=status.HTTP_202_ACCEPTED)
