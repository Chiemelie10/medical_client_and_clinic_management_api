from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from .views import AuthView


urlpatterns = [
    path("register/", AuthView.as_view({"post": "register_user"}), name="register"),
    path("login/", AuthView.as_view({"post": "login_user"}), name="login"),
    path("logout/", AuthView.as_view({"post": "logout_user"}), name="logout"),
    path("revoke-tokens/", AuthView.as_view({"post": "revoke_all_user_tokens"}), name="revoke_tokens"),
    path('request-otp/', AuthView.as_view({"post": "request_otp"}), name="request_otp"),
    path('verify-email/', AuthView.as_view({"post": "verify_email"}), name="verify_email"),
    path('password-reset/', AuthView.as_view({"post": "reset_password"}), name="reset_password"),
    path('validate-otp/', AuthView.as_view({"post": "validate_password_reset_otp"}), name="validate_otp"),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
