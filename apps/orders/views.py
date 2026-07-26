from rest_framework import generics, permissions
from apps.orders.models import Order, VendorOrder
from apps.orders.serializers import OrderSerializer, VendorOrderSerializer
from apps.common.permissions import IsVendor
from apps.common.pagination import DefaultPagination

from drf_spectacular.utils import extend_schema, extend_schema_view
# ---------------------------------------------------------
# BUYER APIS
# ---------------------------------------------------------


@extend_schema_view(
    get=extend_schema(summary="List Orders", description="List all orders for the authenticated buyer.", tags=['Orders (Buyer)'])
)
class OrderListView(generics.ListAPIView):
    """
    List all orders for the authenticated buyer.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'vendor_orders__items'
        )

@extend_schema_view(
    get=extend_schema(summary="Retrieve Order", description="Retrieve specific order details for the authenticated buyer.", tags=['Orders (Buyer)'])
)
class OrderDetailView(generics.RetrieveAPIView):
    """
    Retrieve specific order details for the authenticated buyer.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'vendor_orders__items'
        )

# ---------------------------------------------------------
# VENDOR APIS
# ---------------------------------------------------------

@extend_schema_view(
    get=extend_schema(summary="List Vendor Orders", description="List all vendor orders (sub-orders) for the authenticated vendor's shops.", tags=['Orders (Vendor)'])
)
class VendorOrderListView(generics.ListAPIView):
    """
    List all vendor orders(sub-orders) for the authenticated vendor's shops.
    """

    serializer_class = VendorOrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]
    pagination_class = DefaultPagination

    def get_queryset(self):
        # A vendor can only see orders for shops they own
        return VendorOrder.objects.filter(shop__owner=self.request.user).select_related('shop', 'order').prefetch_related('items')

@extend_schema_view(
    get=extend_schema(summary="Retrieve Vendor Order", description="Retrieve a specific vendor order.", tags=['Orders (Vendor)'])
)
class VendorOrderDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific vendor order.
    """
    permission_classes = [permissions.IsAuthenticated, IsVendor]
    serializer_class = VendorOrderSerializer

    def get_queryset(self):
        return VendorOrder.objects.filter(shop__owner=self.request.user).prefetch_related('items')
