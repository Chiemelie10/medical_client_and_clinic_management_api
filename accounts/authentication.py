from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import Token
from .services.auth_service import AuthService


class CustomJwtAuthentication(JWTAuthentication):
    def get_user(self, validated_token: Token):
        """This method attempts to find and return a user using the given validated token."""
        user = super().get_user(validated_token)

        if AuthService.is_token_blacklisted(token=validated_token):
            raise AuthenticationFailed("Token has been revoked.", code="token_revoked")
        
        return user
