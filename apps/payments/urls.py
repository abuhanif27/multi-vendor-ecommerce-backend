from django.urls import path
from apps.payments.views import PaymentInitializeAPIView, StripeWebhookAPIView
from apps.payments.api.webhooks import SSLCommerzWebhookView

urlpatterns = [
    # Initialization
    path("payments/create/", PaymentInitializeAPIView.as_view(), name="payment-create"),
    
    # Webhooks
    path("payments/webhooks/stripe/", StripeWebhookAPIView.as_view(), name="payment-webhook-stripe"),
    
    # Notice: the new view expects an 'action' param
    path("payments/sslcommerz/<str:action>/", SSLCommerzWebhookView.as_view(), name="payment-webhook-sslcommerz"),
]
