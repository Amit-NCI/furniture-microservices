import pytest
from types import SimpleNamespace

from products.permissions import IsAdminUser


@pytest.mark.parametrize(
    "role, authenticated, expected",
    [
        ("admin", True, True),
        ("customer", True, False),
        ("staff", True, False),
        ("superadmin", True, False),
        ("admin", False, False),
    ],
)
def test_admin_permission_role_access(role, authenticated, expected):
    request = SimpleNamespace(
        user=SimpleNamespace(
            role=role,
            is_authenticated=authenticated,
        )
    )

    permission = IsAdminUser()

    assert bool(permission.has_permission(request, None)) is expected


def test_admin_permission_rejects_missing_user():
    request = SimpleNamespace(user=None)

    permission = IsAdminUser()

    assert not permission.has_permission(request, None)
