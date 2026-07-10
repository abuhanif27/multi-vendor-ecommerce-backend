from django.urls import path

from apps.shops.views import (
    ProductListCreateAPIView,
    ProductDetailAPIView,
    MyProductListAPIView,
    ShopDetailAPIView,
    ShopListCreateAPIView,
    MyShopListAPIView,
)

urlpatterns = [
    path('shops/', ShopListCreateAPIView.as_view(), name='shop-list'),
    path(
        "shops/<slug:slug>/",
        ShopDetailAPIView.as_view(),
        name="shop-detail",
    ),
    path(
        'my/shops/',
        MyShopListAPIView.as_view(),
        name='my-shop-list',
    ),
    path(
        "products/",
        ProductListCreateAPIView.as_view(),
        name="product-list",
    ),
    path(
        "products/<slug:slug>/",
        ProductDetailAPIView.as_view(),
        name="product-detail",
    ),
    path(
        "my/products/",
        MyProductListAPIView.as_view(),
        name="my-product-list",
    ),
]
