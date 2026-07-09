from django.urls import path

from apps.shops.views import ProductListCreateApiView

urlpatterns = [
    path(
        "products/",
        ProductListCreateApiView.as_view(),
        name="product-list",
    ),

]
