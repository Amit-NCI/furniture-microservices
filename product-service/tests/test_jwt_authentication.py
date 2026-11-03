import pytest

from rest_framework_simplejwt.exceptions import InvalidToken
from products.authentication import JWTTokenAuthentication


class FakeValidatedToken:
    def __init__(self, payload):
        self.payload = payload


class TestJWTClaimValidation:

    def setup_method(self):
        self.auth = JWTTokenAuthentication()

    def test_valid_customer_claims(self):
        token = FakeValidatedToken({
            "user_id": 1,
            "role": "customer",
        })

        user = self.auth.get_user(token)

        assert user.id == 1
        assert user.role == "customer"
        assert user.is_authenticated is True

    def test_valid_admin_claims(self):
        token = FakeValidatedToken({
            "user_id": "42",
            "role": "admin",
        })

        user = self.auth.get_user(token)

        assert user.id == "42"
        assert user.role == "admin"
        assert user.is_authenticated is True

    def test_valid_staff_claims(self):
        token = FakeValidatedToken({
            "user_id": 2,
            "role": "staff",
        })

        user = self.auth.get_user(token)

        assert user.id == 2
        assert user.role == "staff"
        assert user.is_authenticated is True

    def test_missing_user_id_rejected(self):
        token = FakeValidatedToken({
            "role": "customer",
        })

        with pytest.raises(InvalidToken):
            self.auth.get_user(token)

    def test_missing_role_rejected(self):
        token = FakeValidatedToken({
            "user_id": 1,
        })

        with pytest.raises(InvalidToken):
            self.auth.get_user(token)

    def test_unknown_role_rejected(self):
        token = FakeValidatedToken({
            "user_id": 1,
            "role": "superadmin",
        })

        with pytest.raises(InvalidToken):
            self.auth.get_user(token)

    def test_empty_user_id_rejected(self):
        token = FakeValidatedToken({
            "user_id": "",
            "role": "customer",
        })

        with pytest.raises(InvalidToken):
            self.auth.get_user(token)

    def test_boolean_user_id_rejected(self):
        token = FakeValidatedToken({
            "user_id": True,
            "role": "customer",
        })

        with pytest.raises(InvalidToken):
            self.auth.get_user(token)

    def test_unsupported_user_id_type_rejected(self):
        token = FakeValidatedToken({
            "user_id": ["invalid"],
            "role": "customer",
        })

        with pytest.raises(InvalidToken):
            self.auth.get_user(token)