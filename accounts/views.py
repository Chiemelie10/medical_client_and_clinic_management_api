from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from .services.auth_service import AuthService
from .serializers import (
    ApiErrorResponseSerializer,
    CustomTokenRefreshSerializer,
    LoginUserSerializer,
    LoginResponseSerializer,
    MessageResponseSerializer,
    PasswordResetSerializer,
    ReferenceTokenResponseSerializer,
    RegistrationResponseSerializer,
    RegisterUserSerializer,
    RequestOtpSerializer,
    TokenRefreshResponseSerializer,
    UserDataResponseSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)


class AuthView(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="auth_register",
        summary="Register a user account",
        description=(
            "Creates an email-based user account and sends a six-digit email "
            "verification OTP. Use the returned `reference_token` together with "
            "the emailed OTP at the verify-email endpoint. Passwords are checked "
            "against the configured Django password validators."
        ),
        tags=["Authentication"],
        auth=[],
        request=RegisterUserSerializer,
        responses={
            201: OpenApiResponse(
                response=RegistrationResponseSerializer,
                description="The account was created and a verification OTP was sent.",
            ),
            400: OpenApiResponse(
                response=ApiErrorResponseSerializer,
                description="Invalid fields, weak passwords, mismatched passwords, or an email already in use.",
            ),
        },
        examples=[
            OpenApiExample(
                "Registration request",
                request_only=True,
                value={
                    "email": "ada@clinic.example",
                    "password": "StrongPassphrase!42",
                    "password_confirmation": "StrongPassphrase!42",
                },
            ),
            OpenApiExample(
                "Registration successful",
                response_only=True,
                status_codes=["201"],
                value={
                    "message": "Registration successful. A verification code has been sent to your email.",
                    "reference_token": "1c4f7120-0415-4a7f-9142-c4cb44bb75f0",
                    "data": {
                        "id": "3fdae292-7b93-4396-95c9-5a373ef0576d",
                        "email": "ada@clinic.example",
                        "first_name": None,
                        "last_name": None,
                        "thumbnail": None,
                        "is_active": True,
                        "date_joined": "2026-08-12T08:30:00Z",
                        "updated_at": "2026-08-12T08:30:00Z",
                        "email_verified_at": None,
                    },
                },
            ),
        ],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="register",
        url_name="register"
    )
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
    
    @extend_schema(
        operation_id="auth_login",
        summary="Log in",
        description=(
            "Authenticates an account using its email and password. The access "
            "token is returned in the response body. The refresh token is set in "
            "an HTTP-only `refresh_token` cookie and is intentionally not exposed "
            "in the JSON response."
        ),
        tags=["Authentication"],
        auth=[],
        request=LoginUserSerializer,
        parameters=[
            OpenApiParameter(
                name="Set-Cookie",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                response=[200],
                description=(
                    "Sets the HTTP-only `refresh_token` cookie. It uses "
                    "`SameSite=Lax` and is marked `Secure` outside debug mode."
                ),
            )
        ],
        responses={
            200: OpenApiResponse(
                response=LoginResponseSerializer,
                description="Authentication succeeded.",
            ),
            400: OpenApiResponse(
                response=ApiErrorResponseSerializer,
                description="The submitted email or password field is invalid.",
            ),
            401: OpenApiResponse(
                response=ApiErrorResponseSerializer,
                description="The email and password do not identify a valid account.",
            ),
        },
        examples=[
            OpenApiExample(
                "Login request",
                request_only=True,
                value={"email": "ada@clinic.example", "password": "StrongPassphrase!42"},
            ),
            OpenApiExample(
                "Login successful",
                response_only=True,
                status_codes=["201"],
                value={
                    "message": "Login successful.",
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
                    "data": {
                        "id": "3fdae292-7b93-4396-95c9-5a373ef0576d",
                        "email": "ada@clinic.example",
                        "first_name": "Ada",
                        "last_name": "Okafor",
                        "thumbnail": None,
                        "is_active": True,
                        "date_joined": "2026-08-12T08:30:00Z",
                        "updated_at": "2026-08-12T08:45:00Z",
                        "email_verified_at": "2026-08-12T08:35:00Z",
                    },
                },
            ),
        ],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="login",
        url_name="login"
    )
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
            status=status.HTTP_200_OK
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

    @extend_schema(
        operation_id="auth_logout",
        summary="Log out the current session",
        description=(
            "Revokes the bearer access token used for this request by adding its "
            "JWT identifier to the server-side blacklist until the token expires. "
            "Send the access token as `Authorization: Bearer <token>`."
        ),
        tags=["Authentication"],
        auth=[{"bearerAuth": []}],
        request=None,
        responses={
            200: OpenApiResponse(
                response=MessageResponseSerializer,
                description="The current access token was revoked.",
                examples=[
                    OpenApiExample("Logout successful", value={"message": "Logout successful"})
                ],
            ),
            401: OpenApiResponse(
                response=ApiErrorResponseSerializer,
                description="The bearer token is missing, invalid, expired, or already revoked.",
            ),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="logout",
        url_name="logout"
    )
    def logout_user(self, request: Request):
        """This method logs out a user by blacklisting their access token."""
        access_token = str(request.auth)

        AuthService.blacklist_token(token_string=access_token)

        return Response(
            {
                "message": "Logout successful"
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        operation_id="auth_revoke_all_tokens",
        summary="Revoke all bearer access tokens",
        description=(
            "Records a revocation cutoff for the authenticated user. The custom "
            "JWT authenticator rejects bearer access tokens issued at or before "
            "that cutoff on subsequent protected requests. Send a valid access "
            "token as `Authorization: Bearer <token>`."
        ),
        tags=["Authentication"],
        auth=[{"bearerAuth": []}],
        request=None,
        responses={
            200: OpenApiResponse(
                response=MessageResponseSerializer,
                description="The account-wide bearer-token revocation cutoff was recorded.",
                examples=[
                    OpenApiExample(
                        "Tokens revoked",
                        value={"message": "Tokens revoked successfully."},
                    )
                ],
            ),
            401: OpenApiResponse(
                response=ApiErrorResponseSerializer,
                description="The bearer token is missing, invalid, expired, or revoked.",
            ),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="revoke-tokens",
        url_name="revoke-tokens"
    )
    def revoke_all_user_tokens(self, request: Request):
        """This method logs out a user by blacklisting all their current tokens."""

        AuthService.revoke_user_tokens(user_id=request.user.id)

        return Response(
            {
                "message": "Tokens revoked successfully."
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        operation_id="auth_request_otp",
        summary="Request an OTP",
        description=(
            "Sends a six-digit OTP to an existing account email and returns the "
            "UUID reference token needed to validate it. Use purpose "
            "`email_verification` to verify an account email, or `otp_validation` "
            "to begin password recovery. The OTP expires after the configured "
            "email OTP window."
        ),
        tags=["Authentication"],
        auth=[],
        request=RequestOtpSerializer,
        responses={
            200: OpenApiResponse(
                response=ReferenceTokenResponseSerializer,
                description="The OTP was generated and dispatched.",
            ),
            400: OpenApiResponse(
                response=ApiErrorResponseSerializer,
                description="The email does not exist, is already verified for the requested purpose, or the purpose is invalid.",
            ),
        },
        examples=[
            OpenApiExample(
                "Password-reset OTP request",
                request_only=True,
                value={"email": "ada@clinic.example", "purpose": "otp_validation"},
            ),
            OpenApiExample(
                "OTP sent",
                response_only=True,
                status_codes=["200"],
                value={
                    "message": "OTP sent successfully.",
                    "reference_token": "1c4f7120-0415-4a7f-9142-c4cb44bb75f0",
                },
            ),
        ],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="request-otp",
        url_name="request-otp"
    )
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

    @extend_schema(
        operation_id="auth_verify_email",
        summary="Verify an email address",
        description=(
            "Validates the six-digit email-verification OTP against its reference "
            "token. A successful request marks the account email as verified and "
            "consumes the OTP so it cannot be reused."
        ),
        tags=["Authentication"],
        auth=[],
        request=VerifyEmailSerializer,
        responses={
            200: OpenApiResponse(
                response=UserDataResponseSerializer,
                description="The account email was verified.",
                examples=[
                    OpenApiExample(
                        "Email verified",
                        value={
                            "message": "Email verified successfully.",
                            "data": {
                                "id": "3fdae292-7b93-4396-95c9-5a373ef0576d",
                                "email": "ada@clinic.example",
                                "first_name": "Ada",
                                "last_name": "Okafor",
                                "thumbnail": None,
                                "is_active": True,
                                "date_joined": "2026-08-12T08:30:00Z",
                                "updated_at": "2026-08-12T08:45:00Z",
                                "email_verified_at": "2026-08-12T08:45:00Z",
                            },
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                response=ApiErrorResponseSerializer,
                description="The payload is invalid, or the OTP is incorrect or expired.",
            ),
        },
        examples=[
            OpenApiExample(
                "Verify email request",
                request_only=True,
                value={
                    "otp": "482193",
                    "reference_token": "1c4f7120-0415-4a7f-9142-c4cb44bb75f0",
                },
            ),
            OpenApiExample(
                "Invalid OTP",
                response_only=True,
                status_codes=["400"],
                value={
                    "success": False,
                    "message": "Invalid verification code.",
                    "errors": None,
                },
            ),
        ],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="verify-email",
        url_name="verify-email"
    )
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

    @extend_schema(
        operation_id="auth_validate_password_reset_otp",
        summary="Validate a password-reset OTP",
        description=(
            "Validates the password-reset OTP and its original reference token. "
            "On success, returns a new, short-lived `reference_token` that "
            "authorizes exactly the next password-reset step. The returned token "
            "must be supplied to the password-reset endpoint before its temporary "
            "authorization window expires."
        ),
        tags=["Authentication"],
        auth=[],
        request=VerifyEmailSerializer,
        responses={
            200: OpenApiResponse(
                response=ReferenceTokenResponseSerializer,
                description="The OTP was accepted and a password-change token was issued.",
            ),
            400: OpenApiResponse(
                response=ApiErrorResponseSerializer,
                description="The payload is invalid, or the OTP is incorrect or expired.",
            ),
        },
        examples=[
            OpenApiExample(
                "Validate reset OTP",
                request_only=True,
                value={
                    "otp": "482193",
                    "reference_token": "1c4f7120-0415-4a7f-9142-c4cb44bb75f0",
                },
            ),
            OpenApiExample(
                "Password-change token issued",
                response_only=True,
                status_codes=["200"],
                value={
                    "message": "Password reset OTP validated successfully.",
                    "reference_token": "81694e1e-20c0-4ea0-8cf1-2f8cc2f812b5",
                },
            ),
        ],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="validate-otp",
        url_name="validate-otp"
    )
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
    
    @extend_schema(
        operation_id="auth_reset_password",
        summary="Set a new password",
        description=(
            "Changes the password after password-reset OTP validation. Supply the "
            "short-lived reference token returned by the validate-OTP endpoint. "
            "The two password fields must match, and the new password must satisfy "
            "the configured Django password validators. This endpoint does not "
            "accept the OTP directly."
        ),
        tags=["Authentication"],
        auth=[],
        request=PasswordResetSerializer,
        responses={
            200: OpenApiResponse(
                response=UserDataResponseSerializer,
                description="The password was changed successfully.",
                examples=[
                    OpenApiExample(
                        "Password reset successful",
                        value={
                            "message": "Password reset was successful.",
                            "data": {
                                "id": "3fdae292-7b93-4396-95c9-5a373ef0576d",
                                "email": "ada@clinic.example",
                                "first_name": "Ada",
                                "last_name": "Okafor",
                                "thumbnail": None,
                                "is_active": True,
                                "date_joined": "2026-08-12T08:30:00Z",
                                "updated_at": "2026-08-12T09:00:00Z",
                                "email_verified_at": "2026-08-12T08:45:00Z",
                            },
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                response=ApiErrorResponseSerializer,
                description="The passwords do not match or the new password fails validation.",
            ),
            401: OpenApiResponse(
                response=ApiErrorResponseSerializer,
                description="The password-change reference token is invalid or expired, or its user no longer exists.",
            ),
        },
        examples=[
            OpenApiExample(
                "Reset password request",
                request_only=True,
                value={
                    "new_password": "NewStrongPassphrase!57",
                    "new_password_confirmation": "NewStrongPassphrase!57",
                    "reference_token": "81694e1e-20c0-4ea0-8cf1-2f8cc2f812b5",
                },
            ),
            OpenApiExample(
                "Password mismatch",
                response_only=True,
                status_codes=["400"],
                value={
                    "success": False,
                    "message": "Validation failed.",
                    "errors": {
                        "new_password_confirmation": ["Passwords do not match."]
                    },
                },
            ),
        ],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="password-reset",
        url_name="password-reset"
    )
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


class CustomTokenRefreshView(TokenRefreshView):
    """Rotate the refresh cookie and return a new access token."""

    serializer_class = CustomTokenRefreshSerializer

    @extend_schema(
        operation_id="auth_refresh_token",
        summary="Refresh an access token",
        description=(
            "Reads the signed JWT from the HTTP-only `refresh_token` cookie, "
            "rejects it if it has been revoked in Redis, and rotates it. The new "
            "access token is returned in the response body and the rotated refresh "
            "token replaces the existing HTTP-only cookie. The submitted refresh "
            "token is revoked after a successful rotation and cannot be reused."
        ),
        tags=["Authentication"],
        auth=[],
        request=None,
        parameters=[
            OpenApiParameter(
                name="Set-Cookie",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                response=[200],
                description=(
                    "Replaces `refresh_token` with the rotated JWT. The cookie is "
                    "HTTP-only, uses `SameSite=Lax`, and is `Secure` outside debug mode."
                ),
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=TokenRefreshResponseSerializer,
                description="The refresh token was rotated and a new access token was issued.",
                examples=[
                    OpenApiExample(
                        "Token refreshed",
                        value={
                            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."
                        },
                    )
                ],
            ),
            401: OpenApiResponse(
                response=ApiErrorResponseSerializer,
                description=(
                    "The refresh cookie is missing, expired, malformed, or revoked, "
                    "or its account is inactive."
                ),
                examples=[
                    OpenApiExample(
                        "Refresh token revoked",
                        value={
                            "success": False,
                            "message": "The refresh token has been revoked.",
                            "errors": None,
                        },
                    )
                ],
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise NotAuthenticated("Refresh token cookie was not provided.")

        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)

        rotated_refresh_token = serializer.validated_data.get("refresh")
        response = Response(
            {
                "access_token": serializer.validated_data["access"]
            },
            status=status.HTTP_200_OK,
        )

        if rotated_refresh_token:
            response.set_cookie(
                key="refresh_token",
                value=rotated_refresh_token,
                max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
            )

        return response
