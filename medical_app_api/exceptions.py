import logging

from django.core.exceptions import (
    ObjectDoesNotExist,
    PermissionDenied as DjangoPermissionDenied
)
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import (
    InvalidToken,
    AuthenticationFailed as SimpleJwtAuthenticationFailed
)


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Global exception handler for a consistent API error response:

    {
        "success": false,
        "message": "...",
        "errors": {...}
    }
    """

    response = exception_handler(exc, context)

    # -----------------------------
    # Validation errors
    # -----------------------------
    if isinstance(exc, ValidationError):
        return Response(
            {
                "success": False,
                "message": "Validation failed.",
                "errors": response.data if response else {},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # -----------------------------
    # Authentication
    # -----------------------------
    if isinstance(
        exc,
        (InvalidToken, SimpleJwtAuthenticationFailed)
    ):
        detail = exc.detail

        if isinstance(detail, dict):
            message = detail.get("detail", "Invalid or expired token.",)
        else:
            message = detail

        return Response(
            {
                "success": False,
                "message": str(message),
                "errors": None,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, NotAuthenticated):
        return Response(
            {
                "success": False,
                "message": "Authentication credentials were not provided.",
                "errors": None,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, AuthenticationFailed):
        detail = exc.detail

        if isinstance(detail, dict):
            message = detail.get("detail", "Unauthenticated.")
        else:
            message = detail

        return Response(
            {
                "success": False,
                "message": str(exc.detail),
                "errors": None,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # -----------------------------
    # Permission
    # -----------------------------
    if isinstance(
        exc,
        (PermissionDenied, DjangoPermissionDenied),
    ):
        return Response(
            {
                "success": False,
                "message": "You do not have permission to perform this action.",
                "errors": None,
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # -----------------------------
    # Not found
    # -----------------------------
    if isinstance(exc, (NotFound, Http404)):
        return Response(
            {
                "success": False,
                "message": "The requested resource was not found.",
                "errors": None,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, ObjectDoesNotExist):
        return Response(
            {
                "success": False,
                "message": str(exc),
                "errors": None,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # -----------------------------
    # Throttling
    # -----------------------------
    if isinstance(exc, Throttled):
        return Response(
            {
                "success": False,
                "message": "Too many requests. Please try again later.",
                "errors": None,
                "retry_after": exc.wait,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # -----------------------------
    # Other DRF exceptions
    # -----------------------------
    if response is not None:
        message = "Request failed."

        if isinstance(response.data, dict):
            detail = response.data.get("detail")

            if isinstance(detail, dict):
                message = detail.get("detail", message)
            else:
                message = str(detail)

        return Response(
            {
                "success": False,
                "message": message,
                "errors": None,
            },
            status=response.status_code,
        )

    # -----------------------------
    # Unexpected server errors
    # -----------------------------
    logger.exception(
        "Unhandled API exception",
        exc_info=exc,
        extra={
            "view": context.get("view").__class__.__name__
            if context.get("view")
            else None,
        },
    )

    return Response(
        {
            "success": False,
            "message": "An unexpected error occurred.",
            "errors": None,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
