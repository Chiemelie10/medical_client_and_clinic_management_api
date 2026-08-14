import hashlib
import secrets
import time
import uuid
from access_control.models import ClinicUserGroup
from accounts.exceptions import InvalidOTP, ExpiredOTP
from accounts.tasks import (
    send_email_verification_otp,
    send_password_reset_otp
)
from clinics.models import Clinic
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import UntypedToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


User = get_user_model()

class AuthService:
    PURPOSE_EMAIL_VERIFICATION = "email_verification"
    PURPOSE_OTP_VALIDATION = "otp_validation"
    PURPOSE_PASSWORD_RESET = "password_reset"
    PURPOSE_JWT_BLACKLIST = "jwt_blacklist"
    PURPOSE_JWT_REVOKED_BEFORE = "jwt_revoked_before"

    @classmethod
    def register_user(cls, *, email: str, password: str):
        """This function registers/creates a new user account."""

        user = User.objects.create_user(email=email, password=password)

        reference_token = cls.request_otp(
            email=email,
            purpose=cls.PURPOSE_EMAIL_VERIFICATION
        )

        return {"user": user, "reference_token": reference_token}

    @classmethod
    def _cache_key(cls, *, reference_token: str, purpose: str) -> str:
        """Returns the string to be used as redis cache key for email OTP."""

        return f"{purpose}:{reference_token}"

    @staticmethod
    def _hash_otp(*, otp: str) -> str:
        """Returns the hashed version of the OTP."""

        return hashlib.sha256(otp.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_otp() -> str:
        """Returns the generated 6 digit OTP."""

        return f"{secrets.randbelow(1_000_000):06d}"

    @classmethod
    def create_otp(cls, *, email: str, purpose: str) -> tuple[str, str]:
        """Caches and returns generated OTP."""
        otp = cls.generate_otp()
        reference_token = uuid.uuid4()

        cache.set(
            key=cls._cache_key(
                reference_token=reference_token,
                purpose=purpose
            ),
            value={
                "email": email,
                "otp_hash": cls._hash_otp(otp=otp),
            },
            timeout=settings.EMAIL_OTP_EXPIRATION
        )

        return otp, reference_token

    @classmethod
    def request_otp(cls, *, email: str, purpose: str) -> str:
        """This method sends OTP to the provided email"""

        otp, reference_token = cls.create_otp(email=email, purpose=purpose)

        if purpose == cls.PURPOSE_EMAIL_VERIFICATION:
            send_email_verification_otp.delay(email, otp)

        elif purpose == cls.PURPOSE_OTP_VALIDATION:
            send_password_reset_otp(email, otp)

        return reference_token

    @classmethod
    def validate_email_verification_otp(cls, *, reference_token: str, otp: str):
        """
        This method validates the otp from the request with that in cache,
        and updates email_verified_at field of the User model.
        """

        key = cls._cache_key(
            reference_token=reference_token,
            purpose=cls.PURPOSE_EMAIL_VERIFICATION
        )

        data = cache.get(key)

        if data is None:
            raise ExpiredOTP()

        submitted_hash = cls._hash_otp(otp=otp)

        if submitted_hash != data["otp_hash"]:
            raise InvalidOTP()

        user = User.objects.filter(email__iexact=data["email"]).first()

        if user is None:
            raise InvalidOTP()

        user.email_verified_at = timezone.now()
        user.save()

        cache.delete(key)

        return user
    
    @classmethod
    def validate_password_reset_otp(cls, *, reference_token: str, otp: str):
        """This method validates the otp from the request with that in cache."""

        otp_validation_key = cls._cache_key(
            reference_token=reference_token,
            purpose=cls.PURPOSE_OTP_VALIDATION
        )

        data = cache.get(otp_validation_key)

        if data is None:
            raise ExpiredOTP()

        submitted_hash = cls._hash_otp(otp=otp)

        if submitted_hash != data["otp_hash"]:
            raise InvalidOTP()

        reference_token = uuid.uuid4()

        user_id = User.objects.filter(email__iexact=data["email"]).values_list('id', flat=True).first()

        if user_id is None:
            raise InvalidOTP()

        cache.delete(otp_validation_key)

        cache.set(
            key=cls._cache_key(
                reference_token=reference_token,
                purpose=cls.PURPOSE_PASSWORD_RESET
            ),
            value={
                "user_id": user_id,
            },
            timeout=settings.CHANGE_PASSWORD_EXPIRATION
        )

        return reference_token

    @classmethod
    def reset_password(cls, *, new_password: str, user):
        """This method changes the password of the provided user."""

        user.set_password(new_password)
        user.save()

        return user

    @classmethod
    def get_tokens_for_user(cls, *, user) -> dict[str, str]:
        """This function generates access and refresh token for the user."""
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @classmethod
    def login_user(cls, *, request: Request, email: str, password: str):
        """This method authenticates a user."""
        user = authenticate(request=request._request, email=email, password=password)

        if user is None:
            raise AuthenticationFailed("Invalid email or password")

        user.last_login = timezone.now()

        user.save()

        tokens = cls.get_tokens_for_user(user=user)

        return {
            "user": user,
            "access": tokens["access"],
            "refresh": tokens["refresh"]
        }

    @classmethod
    def blacklist_token(cls, *, token_string: str) -> bool:
        """This method blacklists a jwt token by adding it to the redis cache."""

        try:
            token = UntypedToken(token_string)
            jti = token.get("jti")
            exp = token.get("exp")

            if not jti or not exp:
                return False
            
            now = int(time.time())
            time_left = exp - now

            if time_left > 0:         
                cache_key = cls._cache_key(
                    reference_token=jti,
                    purpose=cls.PURPOSE_JWT_BLACKLIST
                )

                cache.set(
                    key=cache_key,
                    value="1",
                    timeout=time_left
                )

                return True
        except TokenError:
            return False

        return False
    
    @classmethod
    def revoke_user_tokens(cls, *, user_id: str) -> bool:
        """Revoke all tokens issued to the user before the current time."""
        revoked_at = int(time.time())

        cache_key = cls._cache_key(
            reference_token=user_id,
            purpose=cls.PURPOSE_JWT_REVOKED_BEFORE,
        )

        timeout = int(
            settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
        )

        cache.set(
            key=cache_key,
            value=revoked_at,
            timeout=timeout,
        )

        return True

    @classmethod
    def is_token_blacklisted(cls, *, token: UntypedToken) -> bool:
        """This method checks if a jwt token is blacklisted."""

        jti = token.get("jti")
        user_id = token.get("user_id")
        issued_at = token.get("iat")

        if not jti:
            return True

        blacklist_key = cls._cache_key(
            reference_token=jti,
            purpose=cls.PURPOSE_JWT_BLACKLIST
        )

        if cache.get(blacklist_key) is not None:
            return True
        
        if not user_id or not issued_at:
            return True
        
        revoked_before_key = cls._cache_key(
            reference_token=str(user_id),
            purpose=cls.PURPOSE_JWT_REVOKED_BEFORE,
        )

        revoked_at = cache.get(revoked_before_key)

        if revoked_at is None:
            return False

        return int(issued_at) <= int(revoked_at)

    @classmethod
    def me(cls, *, user_id: str):
        """Returns the user details"""
        roles_prefetch = Prefetch(
            "user_groups",
            queryset=ClinicUserGroup.objects.filter(
                user_id=user_id,
                is_active=True
            ).select_related("group"),
            to_attr="user_roles_at_clinic"
        )

        user = (
            User.objects
            .prefetch_related(
                Prefetch(
                    "clinics_joined",
                    queryset=Clinic.objects.filter(
                        is_active=True,
                        memberships__user_id=user_id,
                        memberships__is_active=True,
                    )
                    .distinct()
                    .order_by("name")
                    .prefetch_related(roles_prefetch)
                )
            )
            .get(pk=user_id)
        )

        return user
