from django.urls import path
from .views import ApproveVendorView, SuspendVendorView, RestoreVendorView

urlpatterns = [
    path('vendors/<uuid:shop_id>/approve/', ApproveVendorView.as_view(), name='admin-vendor-approve'),
    path('vendors/<uuid:shop_id>/suspend/', SuspendVendorView.as_view(), name='admin-vendor-suspend'),
    path('vendors/<uuid:shop_id>/restore/', RestoreVendorView.as_view(), name='admin-vendor-restore'),
]
