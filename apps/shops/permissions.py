from rest_framework.permissions import BasePermission

from apps.accounts.choices import UserRole


class IsVendor(BasePermission):
    message = "Only vendors can perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.VENDOR
        )


class IsProductOwner(BasePermission):
    message = "You do not have permission to perform this action on this product."

    def has_object_permission(self, request, view, obj):
        return obj.shop.owner == request.user


class IsShopOwner(BasePermission):
    message = "You do not have permission to perform this action on this shop."

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
