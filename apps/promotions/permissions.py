from rest_framework import permissions

class IsVendorOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow vendors to edit their own promotions.
    Admins can edit any promotion.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # If it's a marketplace-wide promo, only admins can edit
        if obj.shop is None:
            return False
            
        # Vendors can edit their own shop's promotions
        shop = request.user.shops.first()
        return bool(shop and shop == obj.shop)
