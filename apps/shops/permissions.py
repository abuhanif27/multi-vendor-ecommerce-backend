from rest_framework.permissions import BasePermission

from apps.accounts.models import UserRole


class IsVendor(BasePermission):
    message = "Only vendors can perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.VENDOR
        )
