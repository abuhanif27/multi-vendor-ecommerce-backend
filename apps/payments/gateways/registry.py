from apps.payments.gateways.base import PaymentGateway

class PaymentGatewayRegistry:
    def __init__(self):
        self._gateways = {}
        
    def register(self, name: str, gateway: PaymentGateway):
        self._gateways[name] = gateway
        
    def get(self, name: str) -> PaymentGateway:
        gateway = self._gateways.get(name)
        if not gateway:
            raise ValueError(f"Gateway '{name}' is not registered.")
        return gateway

# Global registry instance
gateway_registry = PaymentGatewayRegistry()
