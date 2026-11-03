import pytest
from types import SimpleNamespace

from products.permissions import IsStaffUser, IsCustomerOrStaff


@pytest.mark.parametrize(
    "role, authenticated, staff_allowed, customer_or_staff_allowed",
    [
        ("customer", True, False, True),
        ("staff", True, True, True),
        ("admin", True, False, False),
        ("superadmin", True, False, False),
        ("customer", False, False, False),
        ("staff", False, False, False),
        ("admin", False, False, False),
    ],
)
def test_existing_product_permissions(
    role, authenticated, staff_allowed, customer_or_staff_allowed
):
    request = SimpleNamespace(
        user=SimpleNamespace(
            role=role,
            is_authenticated=authenticated,
        )
    )

    assert bool(IsStaffUser().has_permission(request, None)) is staff_allowed
    assert bool(
        IsCustomerOrStaff().has_permission(request, None)
    ) is customer_or_staff_allowed


def test_existing_product_permissions_reject_missing_user():
    request = SimpleNamespace(user=None)

    assert not IsStaffUser().has_permission(request, None)
    assert not IsCustomerOrStaff().has_permission(request, None)
