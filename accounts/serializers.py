from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from .services.auth_service import AuthService


User = get_user_model()

class RegisterUserSerializer(serializers.Serializer):
    """This class validates user registration request."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        - Validates password rules.
        - Checks if password and password confirmation fields match.
        """

        password = data.get("password")
        password_confirmation = data.get("password_confirmation")
        email = data.get("email")

        temp_user = User(email=email, password=password)

        try:
            validate_password(password, user=temp_user)
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        if password != password_confirmation:
            raise serializers.ValidationError({"password_confirmation": "Passwords do not match."})

        return data

    def validate_email(self, value: str) -> str:
        """This method validates the email field."""
        email = value.strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        return email
    

class LoginUserSerializer(serializers.Serializer):
    """This class validates user login request."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "thumbnail",
            "is_active",
            "date_joined",
            "updated_at",
            "email_verified_at"
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")
        is_registration = self.context.get("is_registration", False)

        is_owner = (
            request
            and request.user
            and request.user.is_authenticated
            and request.user.id == instance.id
        )

        if not is_owner and not is_registration:
            data["email"] = ""

        return data


class VerifyEmailSerializer(serializers.Serializer):
    """This class validates email verification request."""
    otp = serializers.CharField()
    reference_token = serializers.CharField()


class PasswordResetSerializer(serializers.Serializer):
    """This class validates password reset request."""
    new_password = serializers.CharField()
    new_password_confirmation = serializers.CharField(write_only=True)
    reference_token = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        - Validates password rules.
        - Checks if password and password confirmation fields match.
        - Validates that same user that received and submitted the OTP is the one changing the password.
        """

        new_password = data.get("new_password")
        new_password_confirmation = data.get("new_password_confirmation")
        reference_token = data.get("reference_token")

        if new_password != new_password_confirmation:
            raise serializers.ValidationError({"new_password_confirmation": "Passwords do not match."})
        
        password_reset_key = AuthService._cache_key(
            reference_token=reference_token,
            purpose=AuthService.PURPOSE_PASSWORD_RESET
        )

        cached_data = cache.get(password_reset_key)

        if cached_data is None:
            raise AuthenticationFailed("User not recognised.")

        try:
            user = User.objects.get(id=cached_data["user_id"])
            validate_password(new_password, user=user)

        except User.DoesNotExist:
            raise AuthenticationFailed("User not recognised.")

        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        
        data["user"] = user

        return data


class RequestOtpSerializer(serializers.Serializer):
    """This class validates email verification or password reset OTP request."""

    PURPOSE_CHOICES = [
        (AuthService.PURPOSE_EMAIL_VERIFICATION, "Email Verification"),
        (AuthService.PURPOSE_OTP_VALIDATION, "OTP Validation")
    ]

    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=PURPOSE_CHOICES)

    def validate(self, data):
        """This method validates the email field."""
        email = data.get("email")
        purpose = data.get("purpose")

        user = User.objects.filter(email__iexact=email).values('id', 'email_verified_at').first()

        if user is None:
            raise serializers.ValidationError({"email": "Email was not found."})

        if purpose == AuthService.PURPOSE_EMAIL_VERIFICATION and user.email_verified_at:
            raise serializers.ValidationError({"email": "Email has already been verified."})

        return data


# Response serializers used by the generated OpenAPI documentation.
class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class ReferenceTokenResponseSerializer(MessageResponseSerializer):
    reference_token = serializers.UUIDField()


class UserDataResponseSerializer(MessageResponseSerializer):
    data = UserSerializer(read_only=True)


class RegistrationResponseSerializer(ReferenceTokenResponseSerializer):
    data = UserSerializer(read_only=True)


class LoginResponseSerializer(UserDataResponseSerializer):
    access_token = serializers.CharField()


class ApiErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    errors = serializers.JSONField(required=False, allow_null=True)
