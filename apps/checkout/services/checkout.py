from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from apps.cart.services.cart import CartService
from apps.inventory.services.inventory import InventoryService
from apps.cart.models import Cart

class CheckoutService:
    @staticmethod
    def get_checkout_summary(user):
        """
        Builds the checkout summary.
        Reads the user's active cart and dynamically calculates totals.
        """
        cart = CartService.get_or_create_cart(user)
        items = cart.items.select_related('variant__product__shop', 'variant__inventory').all()
        
        if not items.exists():
            raise ValidationError("Cart is empty.")
            
        subtotal = Decimal('0.00')
        inventory_warnings = []
        price_warnings = []
        unavailable_items = []
        
        cart_items_data = []
        
        for item in items:
            variant = item.variant
            inventory = variant.inventory
            
            # Check inventory
            available = inventory.quantity_on_hand - inventory.quantity_reserved
            if available < item.quantity:
                unavailable_items.append(variant.sku)
                inventory_warnings.append(
                    f"Insufficient stock for {variant.sku}. Requested: {item.quantity}, Available: {available}."
                )
                
            # Check price changes
            if item.unit_price != variant.price:
                price_warnings.append(
                    f"Price for {variant.sku} changed from {item.unit_price} to {variant.price}."
                )
                
            # Compute based on LIVE price (as it's dynamic)
            item_total = variant.price * item.quantity
            subtotal += item_total
            
            cart_items_data.append({
                "id": str(item.id),
                "sku": variant.sku,
                "product_name": variant.product.name,
                "shop_name": variant.product.shop.name,
                "quantity": item.quantity,
                "unit_price": variant.price,
                "item_total": item_total,
            })
            
        # Simplified for now (future: discounts, taxes, shipping)
        discounts = Decimal('0.00')
        shipping = Decimal('0.00')
        taxes = Decimal('0.00')
        total = subtotal - discounts + shipping + taxes
        
        return {
            "items": cart_items_data,
            "subtotal": subtotal,
            "discounts": discounts,
            "shipping": shipping,
            "taxes": taxes,
            "total": total,
            "warnings": {
                "inventory": inventory_warnings,
                "price": price_warnings,
                "unavailable_items": unavailable_items,
            }
        }

    @staticmethod
    @transaction.atomic
    def process_checkout(user, shipping_address, billing_address=None):
        """
        Validates cart, reserves inventory, and builds the order DTO payload.
        Rolls back entirely if any validation or reservation fails.
        """
        summary = CheckoutService.get_checkout_summary(user)
        
        # 1. Check for warnings that block checkout
        if summary["warnings"]["inventory"] or summary["warnings"]["unavailable_items"]:
            raise ValidationError("Cannot proceed: some items have insufficient inventory.")
            
        if summary["warnings"]["price"]:
            raise ValidationError("Cannot proceed: prices have changed. Please review your cart.")
            
        # 2. Reserve inventory
        cart = CartService.get_or_create_cart(user)
        items = cart.items.select_related('variant__product__shop', 'variant__inventory').all()
        
        vendor_orders = {}
        
        for item in items:
            # Atomic reservation for each item
            InventoryService.reserve_stock(item.variant.inventory.id, item.quantity)
            
            # Group by shop (vendor)
            shop_id = str(item.variant.product.shop.id)
            if shop_id not in vendor_orders:
                vendor_orders[shop_id] = {
                    "vendor_subtotal": Decimal('0.00'),
                    "items": []
                }
                
            item_total = item.variant.price * item.quantity
            vendor_orders[shop_id]["vendor_subtotal"] += item_total
            vendor_orders[shop_id]["items"].append(item)
            
            # Update the snapshot to lock the price at checkout
            item.unit_price = item.variant.price
            item.save(update_fields=['unit_price'])

        # 3. Change Cart status to prevent further modification
        cart.status = Cart.CartStatus.CHECKED_OUT
        cart.save(update_fields=['status'])

        # 4. Construct Order DTO
        dto = {
            "user": user,
            "shipping_address": shipping_address,
            "billing_address": billing_address or shipping_address,
            "cart_id": str(cart.id),
            "financials": {
                "subtotal": summary["subtotal"],
                "shipping_total": summary["shipping"],
                "tax_total": summary["taxes"],
                "grand_total": summary["total"],
            },
            "vendor_orders": vendor_orders
        }
        
        # Future: return OrderService.create_order(dto)
        # For now, return the DTO or a mock success response
        return dto
