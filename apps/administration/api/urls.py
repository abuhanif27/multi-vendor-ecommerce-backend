from django.urls import path
from .views import ApproveVendorView, SuspendVendorView, RestoreVendorView, RejectVendorView
from .products import ApproveProductView, RejectProductView, SuspendProductView, RestoreProductView
from .reviews import (
    HideProductReviewView, RemoveProductReviewView, RestoreProductReviewView,
    HideShopReviewView, RemoveShopReviewView, RestoreShopReviewView
)

urlpatterns = [
    path('vendors/<uuid:shop_id>/approve/', ApproveVendorView.as_view(), name='admin-vendor-approve'),
    path('vendors/<uuid:shop_id>/suspend/', SuspendVendorView.as_view(), name='admin-vendor-suspend'),
    path('vendors/<uuid:shop_id>/restore/', RestoreVendorView.as_view(), name='admin-vendor-restore'),
    path('vendors/<uuid:shop_id>/reject/', RejectVendorView.as_view(), name='admin-vendor-reject'),
    
    path('products/<uuid:product_id>/approve/', ApproveProductView.as_view(), name='admin-product-approve'),
    path('products/<uuid:product_id>/reject/', RejectProductView.as_view(), name='admin-product-reject'),
    path('products/<uuid:product_id>/suspend/', SuspendProductView.as_view(), name='admin-product-suspend'),
    path('products/<uuid:product_id>/restore/', RestoreProductView.as_view(), name='admin-product-restore'),

    path('reviews/product/<uuid:review_id>/hide/', HideProductReviewView.as_view(), name='admin-product-review-hide'),
    path('reviews/product/<uuid:review_id>/remove/', RemoveProductReviewView.as_view(), name='admin-product-review-remove'),
    path('reviews/product/<uuid:review_id>/restore/', RestoreProductReviewView.as_view(), name='admin-product-review-restore'),

    path('reviews/shop/<uuid:review_id>/hide/', HideShopReviewView.as_view(), name='admin-shop-review-hide'),
    path('reviews/shop/<uuid:review_id>/remove/', RemoveShopReviewView.as_view(), name='admin-shop-review-remove'),
    path('reviews/shop/<uuid:review_id>/restore/', RestoreShopReviewView.as_view(), name='admin-shop-review-restore'),
]
