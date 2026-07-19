from rest_framework.permissions import BasePermission

class IsInventoryOwner(BasePermission):
    """
    Allows access only to the owner of the inventory.

    Expected object:
        Inventory
    """

    message = (
        "You do not have permission to perform "
        "this action on this inventory."
    )

    def has_permission(self, request, view):
        if request.method != "POST":
            return True

        variant = view.get_variant()
        return (
            request.user.is_authenticated
            and variant.product.shop.owner == request.user
        )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return (
            obj.variant.product.shop.owner
            == request.user
        )
