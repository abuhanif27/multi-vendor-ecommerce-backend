from django.urls import path
from .views import ApproveVendorView, SuspendVendorView, RestoreVendorView, RejectVendorView

urlpatterns = [
    path('vendors/<uuid:shop_id>/approve/', ApproveVendorView.as_view(), name='admin-vendor-approve'),
    path('vendors/<uuid:shop_id>/suspend/', SuspendVendorView.as_view(), name='admin-vendor-suspend'),
    path('vendors/<uuid:shop_id>/restore/', RestoreVendorView.as_view(), name='admin-vendor-restore'),
    path('vendors/<uuid:shop_id>/reject/', RejectVendorView.as_view(), name='admin-vendor-reject'),
]
