from django.urls import path
from apps.cart.views import (
    CartRetrieveAPIView,
    CartItemCollectionAPIView,
    CartItemDetailAPIView,
)

urlpatterns = [
    path("", CartRetrieveAPIView.as_view(), name="cart-detail"),
    path("items/", CartItemCollectionAPIView.as_view(), name="cart-items"),
    path("items/<uuid:pk>/", CartItemDetailAPIView.as_view(), name="cart-item-detail"),
]
