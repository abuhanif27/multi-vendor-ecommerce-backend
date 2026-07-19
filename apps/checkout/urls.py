from django.urls import path
from apps.checkout.views import CheckoutAPIView

urlpatterns = [
    path("", CheckoutAPIView.as_view(), name="checkout"),
]
