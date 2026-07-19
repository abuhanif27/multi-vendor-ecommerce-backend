from django.urls import path
from apps.inventory.views import (
    InventoryDetailAPIView,
    InventoryTransactionListCreateAPIView,
)

urlpatterns = [
    path(
        "shops/<slug:shop_slug>/products/<slug:product_slug>/variants/<str:sku>/inventory/",
        InventoryDetailAPIView.as_view(),
        name="inventory-detail",
    ),
    path(
        "shops/<slug:shop_slug>/products/<slug:product_slug>/variants/<str:sku>/inventory/transactions/",
        InventoryTransactionListCreateAPIView.as_view(),
        name="inventory-transactions",
    ),
]
