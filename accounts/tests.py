from unittest.mock import Mock, patch

from django.template.loader import render_to_string
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from .serializers import CustomTokenRefreshSerializer
from .views import CustomTokenRefreshView


class EmailVerificationTemplateTests(SimpleTestCase):
    def test_template_renders_verification_details_and_brand_chrome(self):
        html = render_to_string(
            "accounts/emails/email_verification.html",
            {
                "first_name": "Ada",
                "email": "ada@clinic.example",
                "verification_code": "123456",
                "expiration_minutes": 10,
            },
        )

        self.assertIn("NoLineMed", html)
        self.assertIn("Verify your email", html)
        self.assertIn("ada@clinic.example", html)
        self.assertIn("123456", html)
        self.assertIn("expires in 10 minutes", html)
        self.assertIn("#17324D", html)
        self.assertIn("#0F766E", html)

    def test_template_optionally_renders_verification_link(self):
        verification_url = "https://nolinemed.app/verify-email?token=example"

        html = render_to_string(
            "accounts/emails/email_verification.html",
            {
                "email": "ada@clinic.example",
                "verification_code": "123456",
                "verification_url": verification_url,
            },
        )

        self.assertIn(verification_url, html)
        self.assertIn("Verify email address", html)


class PasswordResetOtpTemplateTests(SimpleTestCase):
    def test_template_renders_reset_details_and_brand_chrome(self):
        html = render_to_string(
            "accounts/emails/password_reset_otp.html",
            {
                "first_name": "Ada",
                "email": "ada@clinic.example",
                "otp": "654321",
                "expiration_minutes": 10,
            },
        )

        self.assertIn("NoLineMed", html)
        self.assertIn("Reset your password", html)
        self.assertIn("ada@clinic.example", html)
        self.assertIn("654321", html)
        self.assertIn("expires in 10 minutes", html)
        self.assertIn("your password will remain unchanged", html)
        self.assertIn("#17324D", html)
        self.assertIn("#0F766E", html)

    def test_template_uses_default_expiration_and_generic_greeting(self):
        html = render_to_string(
            "accounts/emails/password_reset_otp.html",
            {
                "email": "ada@clinic.example",
                "otp": "654321",
            },
        )

        self.assertIn("Hello,", html)
        self.assertIn("expires in 10 minutes", html)


class CustomTokenRefreshSerializerTests(SimpleTestCase):
    @patch("accounts.serializers.TokenRefreshSerializer.validate")
    @patch("accounts.serializers.AuthService.blacklist_token")
    @patch("accounts.serializers.AuthService.is_token_blacklisted")
    @patch("accounts.serializers.RefreshToken")
    def test_checks_and_revokes_submitted_token_before_returning_rotation(
        self,
        refresh_token_class,
        is_token_blacklisted,
        blacklist_token,
        parent_validate,
    ):
        submitted_token = Mock()
        refresh_token_class.return_value = submitted_token
        is_token_blacklisted.return_value = False
        parent_validate.return_value = {
            "access": "new-access-token",
            "refresh": "rotated-refresh-token",
        }

        result = CustomTokenRefreshSerializer().validate(
            {"refresh": "submitted-refresh-token"}
        )

        refresh_token_class.assert_called_once_with("submitted-refresh-token")
        is_token_blacklisted.assert_called_once_with(token=submitted_token)
        blacklist_token.assert_called_once_with(
            token_string="submitted-refresh-token"
        )
        self.assertEqual(result["refresh"], "rotated-refresh-token")


class CustomTokenRefreshViewTests(SimpleTestCase):
    def test_rotated_refresh_token_is_set_in_cookie_and_hidden_from_body(self):
        serializer = Mock()
        serializer.validated_data = {
            "access": "new-access-token",
            "refresh": "rotated-refresh-token",
        }
        request = APIRequestFactory().post("/api/v1/auth/token/refresh/")
        request.COOKIES["refresh_token"] = "submitted-refresh-token"

        with patch.object(
            CustomTokenRefreshView,
            "get_serializer",
            return_value=serializer,
        ):
            response = CustomTokenRefreshView.as_view()(request)

        serializer.is_valid.assert_called_once_with(raise_exception=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"access_token": "new-access-token"})
        self.assertEqual(
            response.cookies["refresh_token"].value,
            "rotated-refresh-token",
        )
        self.assertTrue(response.cookies["refresh_token"]["httponly"])
