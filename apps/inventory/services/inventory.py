from django.db import transaction
from apps.inventory.models import Inventory

class InventoryService:
    @staticmethod
    def create_inventory(variant, initial_stock=0):
        """
        Creates an inventory record for a given variant.
        Should be called inside VariantService.create().
        """
        inventory = Inventory.objects.create(
            variant=variant,
            quantity_on_hand=initial_stock
        )
        return inventory

    @staticmethod
    @transaction.atomic
    def increase_stock(inventory_id, quantity, user=None, note="", reference=""):
        from apps.inventory.models import InventoryTransaction
        inventory = Inventory.objects.select_for_update().get(id=inventory_id)
        
        inventory.quantity_on_hand += quantity
        inventory.save(update_fields=["quantity_on_hand"])

        InventoryTransaction.objects.create(
            inventory=inventory,
            transaction_type=InventoryTransaction.TransactionType.IN,
            quantity=quantity,
            note=note,
            reference=reference,
            created_by=user,
        )
        return inventory

    @staticmethod
    @transaction.atomic
    def decrease_stock(inventory_id, quantity, user=None, note="", reference=""):
        from apps.inventory.models import InventoryTransaction
        from django.core.exceptions import ValidationError
        inventory = Inventory.objects.select_for_update().get(id=inventory_id)
        
        if inventory.quantity_on_hand < quantity:
            raise ValidationError("Cannot decrease stock below 0.")
            
        inventory.quantity_on_hand -= quantity
        inventory.save(update_fields=["quantity_on_hand"])

        InventoryTransaction.objects.create(
            inventory=inventory,
            transaction_type=InventoryTransaction.TransactionType.OUT,
            quantity=quantity,
            note=note,
            reference=reference,
            created_by=user,
        )
        return inventory

    @classmethod
    @transaction.atomic
    def adjust_stock(cls, inventory_id, new_quantity, user=None, note="", reference=""):
        from apps.inventory.models import InventoryTransaction
        from django.core.exceptions import ValidationError
        inventory = Inventory.objects.select_for_update().get(id=inventory_id)
        
        if new_quantity < 0:
            raise ValidationError("Inventory quantity cannot be negative.")
            
        old_quantity = inventory.quantity_on_hand
        difference = new_quantity - old_quantity
        
        if difference == 0:
            return inventory
            
        inventory.quantity_on_hand = new_quantity
        inventory.save(update_fields=["quantity_on_hand"])
        
        transaction_type = (
            InventoryTransaction.TransactionType.IN 
            if difference > 0 else 
            InventoryTransaction.TransactionType.OUT
        )

        InventoryTransaction.objects.create(
            inventory=inventory,
            transaction_type=InventoryTransaction.TransactionType.ADJUST,
            quantity=abs(difference),
            note=note,
            reference=reference,
            created_by=user,
        )
        return inventory

    @staticmethod
    @transaction.atomic
    def reserve_stock(inventory_id, quantity):
        from django.core.exceptions import ValidationError
        inventory = Inventory.objects.select_for_update().get(id=inventory_id)
        
        available = inventory.quantity_on_hand - inventory.quantity_reserved
        if available < quantity:
            raise ValidationError(f"Insufficient stock. Available: {available}, Requested: {quantity}")
            
        inventory.quantity_reserved += quantity
        inventory.save(update_fields=["quantity_reserved"])
        return inventory

    @staticmethod
    @transaction.atomic
    def release_stock(inventory_id, quantity):
        from django.core.exceptions import ValidationError
        inventory = Inventory.objects.select_for_update().get(id=inventory_id)
        
        if inventory.quantity_reserved < quantity:
            raise ValidationError("Cannot release more stock than currently reserved.")
            
        inventory.quantity_reserved -= quantity
        inventory.save(update_fields=["quantity_reserved"])
        return inventory
