from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 3,
    },
    enqueue_on_commit=True
)
def send_email_verification_otp(email: str, otp: str):
    """This function sends OTP to the provided email."""

    otp_expiration = settings.EMAIL_OTP_EXPIRATION // 60

    context = {
        "verification_code": otp,
        "email": email,
        "expiration_minutes": otp_expiration
    }

    html_content = render_to_string(
        "accounts/emails/email_verification.html",
        context
    )

    text_coontent = f"Your email verification code is {otp} " \
        f"This code expires in {otp_expiration} minutes."

    email_message = EmailMultiAlternatives(
        subject="Email Verification OTP",
        body=text_coontent,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )

    email_message.attach_alternative(
        html_content, "text/html"
    )

    email_message.send()
