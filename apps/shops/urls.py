from django.urls import path

from apps.shops.views import (
    ShopListCreateAPIView,
    ShopDetailAPIView,
    MyShopListAPIView,
    ProductListCreateAPIView,
    ProductDetailAPIView,
    MyProductListAPIView,
    ProductImageCreateAPIView,
    ProductImageDetailAPIView,
)

from apps.shops.views.variants import (
    ProductVariantDetailAPIView,
    ProductVariantListCreateAPIView,
)

from apps.shops.views.variant_images import (
    VariantImageCreateAPIView,
    VariantImageDetailAPIView,
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
        "shops/<slug:shop_slug>/products/<slug:product_slug>/variants/",
        ProductVariantListCreateAPIView.as_view(),
        name="variant-list-create",
    ),

    path(
        "shops/<slug:shop_slug>/products/<slug:product_slug>/variants/<str:sku>/",
        ProductVariantDetailAPIView.as_view(),
        name="variant-detail",
    ),
    path(
        "my/products/",
        MyProductListAPIView.as_view(),
        name="my-product-list",
    ),
    path(
        "shops/<slug:shop_slug>/products/<slug:product_slug>/images/",
        ProductImageCreateAPIView.as_view(),
        name="product-image-create",
    ),
    path(
        "shops/<slug:shop_slug>/products/<slug:product_slug>/images/<uuid:pk>/",
        ProductImageDetailAPIView.as_view(),
        name="product-image-detail",
    ),
    path(
        "shops/<slug:shop_slug>/products/<slug:product_slug>/variants/<str:sku>/images/",
        VariantImageCreateAPIView.as_view(),
        name="variant-image-create",
    ),
    path(
        "shops/<slug:shop_slug>/products/<slug:product_slug>/variants/<str:sku>/images/<uuid:pk>/",
        VariantImageDetailAPIView.as_view(),
        name="variant-image-detail",
    ),
]
