import uuid
import os
import django
from decimal import Decimal
from django.conf import settings

# Make sure django is set up if running standalone, though manage.py shell handles this.
from apps.accounts.models import User
from apps.shops.models import Shop, Product, ProductVariant
from apps.catalog.models import Category
from apps.inventory.models import Inventory
from apps.cart.services.cart import CartService
from apps.checkout.services.checkout import CheckoutService
from apps.payments.services.payment import PaymentService
from apps.payments.models import Payment


def run_e2e_test():
    print("=== 1. Creating User ===")
    user, _ = User.objects.get_or_create(
        email="e2e_buyer@example.com",
        defaults={"is_active": True, "password": "dummy"}
    )

    vendor_user, _ = User.objects.get_or_create(
        email="e2e_vendor@example.com",
        defaults={"is_active": True, "password": "dummy", "role": "VENDOR"}
    )

    print("=== 2. Creating Shop & Catalog ===")
    shop, _ = Shop.objects.get_or_create(
        owner=vendor_user,
        name="E2E Test Shop",
        defaults={"status": "APPROVED"}
    )

    category, _ = Category.objects.get_or_create(name="E2E Electronics")

    product, _ = Product.objects.get_or_create(
        shop=shop,
        name="E2E Laptop",
        defaults={"description": "Test Laptop",
                  "category": category, "status": "active"}
    )
    product.status = "active"
    product.save()

    variant, _ = ProductVariant.objects.get_or_create(
        product=product,
        sku="E2E-LAPTOP-1",
        defaults={"price": Decimal("500.00"), "status": "active"}
    )
    variant.status = "active"
    variant.save()

    print("=== 3. Setting up Inventory ===")
    inventory, _ = Inventory.objects.get_or_create(
        variant=variant,
        defaults={"quantity_on_hand": 100}
    )
    # Ensure inventory has stock in case it already existed
    inventory.quantity_on_hand = 100
    inventory.quantity_reserved = 0
    inventory.save()

    print("=== 4. Creating Cart & Adding Items ===")
    CartService.add_item(user=user, variant_sku=variant.sku, quantity=2)
    print("Cart added successfully.")

    print("=== 5. Processing Checkout (Order Creation) ===")
    shipping_address = {
        "name": "E2E Buyer",
        "phone": "01700000000",
        "address": "123 E2E Street",
        "city": "Dhaka",
        "country": "Bangladesh"
    }
    order = CheckoutService.process_checkout(
        user=user, shipping_address=shipping_address)
    print(
        f"Order created successfully: {order.id}, Total: {order.grand_total}")

    print("=== 6. Initializing SSLCommerz Payment ===")
    try:
        response = PaymentService.initialize_payment(
            order_id=order.id,
            provider='SSLCOMMERZ',
            return_url_base='http://localhost:8000'
        )
        print("Success! Gateway Response:", response)

        payment = Payment.objects.get(id=response['payment_id'])
        print(f"Payment Record created! Status: {payment.status}")
    except Exception as e:
        print("Failed to initialize payment:", str(e))


if __name__ == "__main__":
    run_e2e_test()
