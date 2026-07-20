from rest_framework import serializers
from apps.payments.models import Payment

class PaymentInitializationSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    provider = serializers.ChoiceField(choices=Payment.Provider.choices)

class PaymentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'provider', 'amount', 'currency', 
            'status', 'paid_at', 'failure_reason', 'created_at'
        ]
