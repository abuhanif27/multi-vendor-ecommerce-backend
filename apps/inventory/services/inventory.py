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
