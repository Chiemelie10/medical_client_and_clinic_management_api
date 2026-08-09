from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the email-based user model."""

    model = User
    ordering = ("-date_joined",)
    list_per_page = 50
    list_select_related = True
    filter_horizontal = ("groups", "user_permissions")

    @admin.display(description="Thumbnail")
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="40" height="40" '
                'style="border-radius:50%;object-fit:cover;" alt="" />',
                obj.thumbnail.url,
            )
        return "-"

    @admin.display(boolean=True, description="Email verified", ordering="email_verified_at")
    def is_email_verified(self, obj):
        return obj.email_verified_at is not None

    list_display = (
        "email",
        "first_name",
        "last_name",
        "thumbnail_preview",
        "is_email_verified",
        "is_active",
        "is_staff",
        "date_joined",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
        ("email_verified_at", admin.EmptyFieldListFilter),
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
    )

    readonly_fields = (
        "id",
        "date_joined",
        "updated_at",
        "last_login",
        "email_verified_at",
        "thumbnail_preview",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "email",
                    "password",
                ),
            },
        ),
        (
            "Personal information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "thumbnail",
                    "thumbnail_preview",
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "fields": (
                    "last_login",
                    "email_verified_at",
                    "date_joined",
                    "updated_at",
                ),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "thumbnail",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )
