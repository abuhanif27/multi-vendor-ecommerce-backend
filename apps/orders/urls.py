from django.urls import path
from apps.orders.views import (
    OrderListView,
    OrderDetailView,
    VendorOrderListView,
    VendorOrderDetailView
)

urlpatterns = [
    # Buyer endpoints
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/<uuid:pk>/", OrderDetailView.as_view(), name="order-detail"),
    
    # Vendor endpoints
    path("vendor-orders/", VendorOrderListView.as_view(), name="vendor-order-list"),
    path("vendor-orders/<uuid:pk>/", VendorOrderDetailView.as_view(), name="vendor-order-detail"),
]
