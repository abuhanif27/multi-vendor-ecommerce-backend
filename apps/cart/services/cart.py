from django.db import transaction
from django.core.exceptions import ValidationError
from apps.cart.models import Cart, CartItem
from apps.shops.models import ProductVariant

class CartService:
    @staticmethod
    def get_or_create_cart(user):
        cart, _ = Cart.objects.get_or_create(
            user=user,
            status=Cart.CartStatus.ACTIVE,
        )
        return cart

    @staticmethod
    @transaction.atomic
    def add_item(user, variant_sku, quantity):
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

        # Lock the cart to serialize access for this user's cart
        cart = CartService.get_or_create_cart(user)
        cart = Cart.objects.select_for_update().get(id=cart.id)
        
        try:
            variant = ProductVariant.objects.select_related('inventory').get(
                sku=variant_sku, 
                status=ProductVariant.VariantStatus.ACTIVE,
                product__status='active'
            )
        except ProductVariant.DoesNotExist:
            raise ValidationError("Variant not found or inactive.")

        item = CartItem.objects.filter(cart=cart, variant=variant).first()
        
        new_quantity = (item.quantity + quantity) if item else quantity

        CartService._validate_inventory(variant, new_quantity)

        if item:
            item.quantity = new_quantity
            item.unit_price = variant.price # Update snapshot to current price
            item.save(update_fields=["quantity", "unit_price", "updated_at"])
        else:
            item = CartItem.objects.create(
                cart=cart,
                variant=variant,
                quantity=quantity,
                unit_price=variant.price
            )
            
        return item

    @staticmethod
    @transaction.atomic
    def update_quantity(user, item_id, quantity):
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

        try:
            item = CartItem.objects.select_for_update().select_related('variant__inventory').get(
                id=item_id, 
                cart__user=user, 
                cart__status=Cart.CartStatus.ACTIVE
            )
        except CartItem.DoesNotExist:
            raise ValidationError("Cart item not found.")

        CartService._validate_inventory(item.variant, quantity)

        item.quantity = quantity
        item.unit_price = item.variant.price # Update snapshot to current price
        item.save(update_fields=["quantity", "unit_price", "updated_at"])
        
        return item

    @staticmethod
    @transaction.atomic
    def remove_item(user, item_id):
        deleted, _ = CartItem.objects.filter(
            id=item_id, 
            cart__user=user, 
            cart__status=Cart.CartStatus.ACTIVE
        ).delete()
        
        if not deleted:
            raise ValidationError("Cart item not found.")
            
    @staticmethod
    @transaction.atomic
    def clear_cart(user):
        CartItem.objects.filter(
            cart__user=user,
            cart__status=Cart.CartStatus.ACTIVE
        ).delete()

    @staticmethod
    def _validate_inventory(variant, requested_quantity):
        if not hasattr(variant, 'inventory'):
            raise ValidationError("No inventory record for this product.")
            
        inventory = variant.inventory
        available = inventory.quantity_on_hand - inventory.quantity_reserved
        
        if available < requested_quantity:
            raise ValidationError(f"Insufficient stock. Only {available} available.")

    @staticmethod
    def validate_cart(user):
        """
        To be called right before checkout.
        Validates inventory and price discrepancies.
        """
        cart = CartService.get_or_create_cart(user)
        items = cart.items.select_related('variant__inventory').all()
        
        errors = []
        for item in items:
            # Check price change
            if item.unit_price != item.variant.price:
                errors.append(f"Price for {item.variant.sku} has changed from {item.unit_price} to {item.variant.price}.")
                
            # Check inventory
            available = item.variant.inventory.quantity_on_hand - item.variant.inventory.quantity_reserved
            if available < item.quantity:
                errors.append(f"Insufficient stock for {item.variant.sku}. Only {available} available.")
                
        if errors:
            raise ValidationError(errors)
        return True
