import uuid
from decimal import Decimal
from apps.accounts.models import User
from apps.orders.models import Order
from apps.payments.services.payment import PaymentService

def test_sslcommerz():
    # 1. Create a dummy user
    user, _ = User.objects.get_or_create(
        email="test_sslcommerz@example.com",
        defaults={"is_active": True, "password": "dummy"}
    )
    
    # 2. Create a dummy order
    order = Order.objects.create(
        user=user,
        status=Order.OrderStatus.PENDING,
        grand_total=Decimal("105.50"),
        shipping_address={"phone": "01700000000"}
    )
    
    print(f"Created Order: {order.id}")
    
    # 3. Initialize Payment
    print("Initializing SSLCommerz Payment...")
    try:
        response = PaymentService.initialize_payment(
            order_id=order.id, 
            provider='SSLCOMMERZ', 
            return_url_base='http://localhost:8000'
        )
        print("Success! Gateway Response:", response)
    except Exception as e:
        print("Failed to initialize payment:", str(e))

test_sslcommerz()
