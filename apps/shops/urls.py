from django.urls import path

from apps.shops.views import (
    ProductListCreateApiView,
    ProductDetailAPIView,
    MyProductListAPIView,
    ShopListCreateAPIView,
    MyShopListAPIView,
)

urlpatterns = [
    path('shops/', ShopListCreateAPIView.as_view(), name='shop-list'),
    path(
        'my/shops/',
        MyShopListAPIView.as_view(),
        name='my-shop-list',
    ),
    path(
        "products/",
        ProductListCreateApiView.as_view(),
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
