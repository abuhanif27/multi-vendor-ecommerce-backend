from rest_framework.permissions import BasePermission

from apps.accounts.choices import UserRole


class IsVendor(BasePermission):
    """
    Allows access only to authenticated vendors.
    """

    message = "Only vendors can perform this action."

    def has_permission(
        self,
        request,
        view,
    ):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.VENDOR
        )


class IsShopOwner(BasePermission):
    """
    Allows access only to the owner of a shop.

    Expected object:
        Shop
    """

    message = (
        "You do not have permission to perform "
        "this action on this shop."
    )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return obj.owner == request.user


class IsProductOwner(BasePermission):
    """
    Allows access only to the owner of a product.
    """

    message = (
        "You do not have permission to perform "
        "this action on this product."
    )

    def has_permission(self, request, view):
        if request.method != "POST":
            return True

        product = view.get_product()

        return (
            request.user.is_authenticated
            and product.shop.owner == request.user
        )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return obj.shop.owner == request.user


class IsVariantOwner(BasePermission):
    """
    Allows access only to the owner of a product variant.

    Expected object:
        ProductVariant
    """

    message = (
        "You do not have permission to perform "
        "this action on this variant."
    )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return (
            obj.product.shop.owner
            == request.user
        )
