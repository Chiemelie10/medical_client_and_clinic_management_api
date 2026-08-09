from rest_framework import status
from rest_framework.exceptions import APIException


class AccountException(APIException):
    """
    Base exception for account-related business errors.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Account request failed."
    default_code = "account_error"


class InvalidOTP(AccountException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid verification code."
    default_code = "invalid_otp"


class ExpiredOTP(AccountException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Verification code has expired."
    default_code = "expired_otp"
