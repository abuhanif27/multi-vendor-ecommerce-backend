from django.urls import path
from .views import ApproveVendorView, SuspendVendorView, RestoreVendorView, RejectVendorView
from .products import ApproveProductView, RejectProductView, SuspendProductView, RestoreProductView

urlpatterns = [
    path('vendors/<uuid:shop_id>/approve/', ApproveVendorView.as_view(), name='admin-vendor-approve'),
    path('vendors/<uuid:shop_id>/suspend/', SuspendVendorView.as_view(), name='admin-vendor-suspend'),
    path('vendors/<uuid:shop_id>/restore/', RestoreVendorView.as_view(), name='admin-vendor-restore'),
    path('vendors/<uuid:shop_id>/reject/', RejectVendorView.as_view(), name='admin-vendor-reject'),
    
    path('products/<uuid:product_id>/approve/', ApproveProductView.as_view(), name='admin-product-approve'),
    path('products/<uuid:product_id>/reject/', RejectProductView.as_view(), name='admin-product-reject'),
    path('products/<uuid:product_id>/suspend/', SuspendProductView.as_view(), name='admin-product-suspend'),
    path('products/<uuid:product_id>/restore/', RestoreProductView.as_view(), name='admin-product-restore'),
]
