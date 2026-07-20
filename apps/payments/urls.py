from django.urls import path
from apps.payments.views import PaymentInitializeAPIView, StripeWebhookAPIView

urlpatterns = [
    # Initialization
    path("payments/create/", PaymentInitializeAPIView.as_view(), name="payment-create"),
    
    # Webhooks
    path("payments/webhooks/stripe/", StripeWebhookAPIView.as_view(), name="payment-webhook-stripe"),
]
