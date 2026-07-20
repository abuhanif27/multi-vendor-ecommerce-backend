from rest_framework import permissions

class IsReviewOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of a review to edit/delete it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the owner of the review.
        return obj.user == request.user
