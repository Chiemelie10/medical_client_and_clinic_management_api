from django.urls import path
from .views import (
    EmailVerificationView,
    RegisterUserView,
)


urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path('verify-email/', EmailVerificationView.as_view({"post": "verify_email"}), name="verify_email"),
    path('request-otp/', EmailVerificationView.as_view({"post": "request_otp"}), name="request_otp"),
]
