from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from .services.auth_service import AuthService
from .serializers import (
    LoginUserSerializer,
    PasswordResetSerializer,
    RegisterUserSerializer,
    RequestOtpSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)


class AuthView(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def register_user(self, request: Request):
        """This methods registers/creates a new user."""
        serializer = RegisterUserSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        email = validated_data.get("email")
        password = validated_data.get("password")

        data = AuthService.register_user(email=email, password=password)

        user_data = UserSerializer(
            data["user"],
            context={
                "request": request,
                "is_registration": True
            }
        ).data

        return Response(
            {
                "message": "Registration successful. A verification code " \
                    "has been sent to your email.",
                "reference_token": data["reference_token"],
                "data": user_data,
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=["post"])
    def login_user(self, request: Request):
        """This method login users by giving access and refresh tokens."""
        serializer = LoginUserSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        email = validated_data.get("email")
        password = validated_data.get("password")

        data = AuthService.login_user(
            request=request,
            email=email,
            password=password
        )

        user_data = UserSerializer(
            data["user"],
            context={
                "request": request,
                "is_registration": True
            }
        ).data

        response = Response(
            {
                "message": "Login successful.",
                "access_token": data["access"],
                "data": user_data,
            },
            status=status.HTTP_201_CREATED
        )

        response.set_cookie(
            key="refresh_token",
            value=data["refresh"],
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
        )

        return response

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout_user(self, request: Request):
        """This method logs out a user by blacklisting their access token."""
        access_token = str(request.auth)

        AuthService.blacklist_token(access_token)

        return Response(
            {
                "message": "Logout successful"
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def revoke_all_user_tokens(self, request: Request):
        """This method logs out a user by blacklisting all their current tokens."""

        AuthService.revoke_user_tokens(user_id=request.user.id)

        return Response(
            {
                "message": "Tokens revoked successfully."
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"])
    def request_otp(self, request: Request):
        """This method sends OTP to the provided email."""
        serializer = RequestOtpSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        email = validated_data.get("email")
        purpose = validated_data.get("purpose")

        reference_token = AuthService.request_otp(email=email, purpose=purpose)

        return Response(
            {
                "message": "OTP sent successfully.",
                "reference_token": reference_token
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"])
    def verify_email(self, request: Request):
        """This method verifies a user's email using provided OTP."""
        serializer = VerifyEmailSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        otp = validated_data.get("otp")
        reference_token = validated_data.get("reference_token")

        user = AuthService.validate_email_verification_otp(
            reference_token=reference_token,
            otp=otp
        )

        user_data = UserSerializer(
            user,
            context={
                "request": request,
                "is_registration": True
            }
        ).data

        return Response(
            {
                "message": "Email verified successfully.",
                "data": user_data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"])
    def validate_password_reset_otp(self, request: Request):
        """The method validates OTP for password reset."""
        serializer = VerifyEmailSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        otp = validated_data.get("otp")
        reference_token = validated_data.get("reference_token")

        reference_token = AuthService.validate_password_reset_otp(
            reference_token=reference_token,
            otp=otp
        )

        return Response(
            {
                "message": "Password reset OTP validated successfully.",
                "reference_token": reference_token
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=["post"])
    def reset_password(self, request: Request):
        """The method changes a user's password."""
        serializer = PasswordResetSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        user = validated_data.get("user")
        new_password = validated_data.get("new_password")

        user = AuthService.reset_password(
            new_password=new_password,
            user=user
        )

        user_data = UserSerializer(
            user,
            context={
                "request": request,
                "is_registration": True
            }
        ).data

        return Response(
            {
                "message": "Password reset was successful.",
                "data": user_data
            },
            status=status.HTTP_200_OK
        )
