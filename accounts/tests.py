from django.template.loader import render_to_string
from django.test import SimpleTestCase


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
