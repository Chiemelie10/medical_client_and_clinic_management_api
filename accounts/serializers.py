from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers


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

class RequestOtpSerializer(serializers.Serializer):
    """This class validates email verification OTP request."""
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        """This method validates the email field."""
        email = value.strip().lower()

        try:
            user = User.objects.only('id', 'email_verified_at').get(email__iexact=email)

            if user.email_verified_at:
                raise serializers.ValidationError("Email has already been verified.")
        except User.DoesNotExist:
            raise serializers.ValidationError("Email was not found.")

        return email
