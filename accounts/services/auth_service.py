import hashlib
import secrets
import uuid
from accounts.exceptions import InvalidOTP, ExpiredOTP
from accounts.tasks import send_email_verification_otp
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone


User = get_user_model()

class AuthService:
    @classmethod
    def register_user(cls, *, email: str, password: str):
        """This function registers/creates a new user account."""

        user = User.objects.create_user(email=email, password=password)

        reference_token = cls.request_otp(email=email)

        return {"user": user, "reference_token": reference_token}

    @classmethod
    def _cache_key(cls, *, reference_token: str) -> str:
        """Returns the string to be used as redis cache key for email OTP."""

        return f"email_verification:{reference_token}"

    @staticmethod
    def _hash_otp(*, otp: str) -> str:
        """Returns the hashed version of the OTP."""

        return hashlib.sha256(otp.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_otp() -> str:
        """Returns the generated 6 digit OTP."""

        return f"{secrets.randbelow(1_000_000):06d}"

    @classmethod
    def create_otp(cls, *, email: str) -> tuple[str, str]:
        """Caches and returns generated OTP."""
        otp = cls.generate_otp()
        reference_token = uuid.uuid4()

        cache.set(
            key=cls._cache_key(reference_token=reference_token),
            value={
                "email": email,
                "otp_hash": cls._hash_otp(otp=otp),
            },
            timeout=settings.EMAIL_OTP_EXPIRATION
        )

        return otp, reference_token

    @classmethod
    def request_otp(cls, *, email: str) -> str:
        """This method sends OTP to the provided email"""

        otp, reference_token = cls.create_otp(email=email)

        send_email_verification_otp.delay(email, otp)

        return reference_token

    @classmethod
    def verify_otp(cls, *, reference_token: str, otp: str):
        """This method validates the otp from the request with that in cache."""

        key = cls._cache_key(reference_token=reference_token)

        data = cache.get(key)

        if data is None:
            raise ExpiredOTP()

        submitted_hash = cls._hash_otp(otp=otp)

        if submitted_hash != data["otp_hash"]:
            raise InvalidOTP()

        user = User.objects.get(email=data["email"])

        user.email_verified_at = timezone.now()
        user.save()

        cache.delete(key)

        return user
