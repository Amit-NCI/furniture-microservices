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
    Allows only authenticated customers and staff.
    """
    def has_permission(self, request, view):
        user = getattr(request, "user", None)

        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) in ("customer", "staff")
        )


class IsAdminUser(BasePermission):
    """
    Allows only authenticated users with the admin JWT role.
    """

    def has_permission(self, request, view):
        user = getattr(request, "user", None)

        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "admin"
        )
