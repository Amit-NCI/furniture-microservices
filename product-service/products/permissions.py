from rest_framework.permissions import BasePermission


class IsStaffUser(BasePermission):
    """
    Checks role claim from JWT token directly. No DB lookup.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', '') == 'staff'
        )


class IsCustomerOrStaff(BasePermission):
    """
    Allows any authenticated user (customer or staff).
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
        )