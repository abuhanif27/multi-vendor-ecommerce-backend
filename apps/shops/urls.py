from django.urls import path

from apps.shops.views import ProductListCreateApiView, ProductDetailAPIView

urlpatterns = [
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
]
