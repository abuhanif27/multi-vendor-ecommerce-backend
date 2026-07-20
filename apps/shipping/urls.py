from django.urls import path
from apps.shipping.views import (
    BuyerShipmentListAPIView,
    VendorShipmentDetailAPIView,
    VendorShipmentAssignCourierAPIView,
    VendorShipmentStatusUpdateAPIView
)

urlpatterns = [
    # Buyer
    path('shipping/my-shipments/', BuyerShipmentListAPIView.as_view(), name='buyer-shipments'),
    
    # Vendor
    path('shipping/shipments/<uuid:pk>/', VendorShipmentDetailAPIView.as_view(), name='vendor-shipment-detail'),
    path('shipping/shipments/<uuid:pk>/assign-courier/', VendorShipmentAssignCourierAPIView.as_view(), name='vendor-shipment-assign-courier'),
    path('shipping/shipments/<uuid:pk>/update-status/', VendorShipmentStatusUpdateAPIView.as_view(), name='vendor-shipment-update-status'),
]
