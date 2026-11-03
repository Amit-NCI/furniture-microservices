from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class TokenUser:
    """
    Lightweight authenticated user built from validated JWT claims.
    No database lookup is performed.
    """

    def __init__(self, user_id, role):
        self.id = user_id
        self.role = role
        self.is_authenticated = True
        self.is_active = True

    def __str__(self):
        return f"TokenUser(id={self.id}, role={self.role})"


class JWTTokenAuthentication(JWTAuthentication):
    """
    Uses SimpleJWT to validate the token, then checks
    application-specific claims before creating TokenUser.
    """

    def get_user(self, validated_token):
        payload = validated_token.payload

        user_id = payload.get("user_id")
        role = payload.get("role")

        if user_id is None or isinstance(user_id, bool):
            raise InvalidToken("Token is missing a valid user_id")

        if not isinstance(user_id, (int, str)):
            raise InvalidToken("Token contains an invalid user_id")

        if isinstance(user_id, str) and not user_id.strip():
            raise InvalidToken("Token contains an empty user_id")

        if role not in ("customer", "staff", "admin"):
            raise InvalidToken("Token contains an invalid role")

        return TokenUser(user_id=user_id, role=role)