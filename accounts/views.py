from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.auth_service import AuthService
from .serializers import (
    RegisterUserSerializer,
    RequestOtpSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)


class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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


class EmailVerificationView(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def request_otp(self, request):
        """This method sends OTP to the provided email."""
        serializer = RequestOtpSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        email = validated_data.get("email")

        reference_token = AuthService.request_otp(email=email)

        return Response(
            {
                "message": "OTP sent successfully.",
                "reference_token": reference_token
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def verify_email(self, request):
        """This method verifies a user's email using provided OTP."""
        serializer = VerifyEmailSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        otp = validated_data.get("otp")
        reference_token = validated_data.get("reference_token")

        user = AuthService.verify_otp(
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
