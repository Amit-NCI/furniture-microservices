from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class TokenUser:
    """
    Lightweight user object built from JWT claims only.
    No database lookup — reads directly from the token payload.
    """
    def __init__(self, payload):
        self.id = payload.get('user_id')
        self.role = payload.get('role', 'customer')
        self.is_authenticated = True
        self.is_active = True

    def __str__(self):
        return f"TokenUser(id={self.id}, role={self.role})"


class JWTTokenAuthentication(JWTAuthentication):
    """
    Validates the token signature only, then builds a
    TokenUser from the payload claims. No DB lookup.
    """
    def get_user(self, validated_token):
        try:
            return TokenUser(validated_token.payload)
        except Exception:
            raise InvalidToken('Token contained no valid user info')