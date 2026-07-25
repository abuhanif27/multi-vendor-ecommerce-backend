from django.apps import AppConfig

class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    verbose_name = 'Payments'

    def ready(self):
        from apps.payments.gateways.registry import gateway_registry
        from apps.payments.gateways.sslcommerz import SSLCommerzGateway
        from apps.payments.gateways.stripe import StripeGateway
        
        gateway_registry.register('SSLCOMMERZ', SSLCommerzGateway())
        gateway_registry.register('STRIPE', StripeGateway())
