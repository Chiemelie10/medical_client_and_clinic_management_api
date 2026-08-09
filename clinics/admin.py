from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Clinic,
    ClinicInvitation,
    ClinicMembership,
    ClinicService,
    ClinicSetting,
    ClinicWorkingDay,
)


class AuditFieldsAdminMixin:
    readonly_fields = ("id", "created_at", "updated_at")
    list_per_page = 50


@admin.register(Clinic)
class ClinicAdmin(AuditFieldsAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "country",
        "state",
        "contact_email",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "country", "state", "created_at")
    search_fields = (
        "name",
        "slug",
        "contact_email",
        "contact_phone_number",
        "owner__email",
    )
    ordering = ("-created_at",)
    autocomplete_fields = ("owner", "country", "state")
    list_select_related = ("owner", "country", "state")
    prepopulated_fields = {"slug": ("name",)}
    date_hierarchy = "created_at"
    readonly_fields = AuditFieldsAdminMixin.readonly_fields + ("logo_preview",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "name",
                    "slug",
                    "owner",
                    "is_active",
                )
            },
        ),
        (
            "Contact and location",
            {
                "fields": (
                    "contact_email",
                    "contact_phone_number",
                    "address",
                    "country",
                    "state",
                )
            },
        ),
        ("Branding", {"fields": ("logo", "logo_preview")}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Logo preview")
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="64" height="64" '
                'style="border-radius:8px;object-fit:cover;" alt="" />',
                obj.logo.url,
            )
        return "-"


@admin.register(ClinicMembership)
class ClinicMembershipAdmin(AuditFieldsAdminMixin, admin.ModelAdmin):
    list_display = ("user", "clinic", "is_active", "created_at")
    list_filter = ("is_active", "clinic", "created_at")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "clinic__name",
        "specializations",
    )
    autocomplete_fields = ("clinic", "user")
    list_select_related = ("clinic", "user")
    date_hierarchy = "created_at"


@admin.register(ClinicSetting)
class ClinicSettingAdmin(AuditFieldsAdminMixin, admin.ModelAdmin):
    list_display = (
        "clinic",
        "timezone",
        "appointment_duration",
        "allow_public_booking",
        "updated_at",
    )
    list_filter = ("allow_public_booking", "timezone")
    search_fields = ("clinic__name", "clinic__contact_email")
    autocomplete_fields = ("clinic",)
    list_select_related = ("clinic",)


@admin.register(ClinicWorkingDay)
class ClinicWorkingDayAdmin(AuditFieldsAdminMixin, admin.ModelAdmin):
    list_display = (
        "clinic_name",
        "day_of_week",
        "open_time",
        "close_time",
        "updated_at",
    )
    list_filter = ("day_of_week",)
    search_fields = ("clinic_setting__clinic__name",)
    autocomplete_fields = ("clinic_setting",)
    list_select_related = ("clinic_setting", "clinic_setting__clinic")

    @admin.display(description="Clinic", ordering="clinic_setting__clinic__name")
    def clinic_name(self, obj):
        return obj.clinic_setting.clinic.name


@admin.register(ClinicInvitation)
class ClinicInvitationAdmin(AuditFieldsAdminMixin, admin.ModelAdmin):
    list_display = ("email", "clinic", "invited_by", "status", "created_at")
    list_filter = ("status", "clinic", "created_at")
    search_fields = ("email", "clinic__name", "invited_by__email")
    autocomplete_fields = ("clinic", "invited_by")
    list_select_related = ("clinic", "invited_by")
    date_hierarchy = "created_at"


@admin.register(ClinicService)
class ClinicServiceAdmin(AuditFieldsAdminMixin, admin.ModelAdmin):
    list_display = ("name", "clinic", "service_cost", "created_at", "updated_at")
    list_filter = ("clinic", "created_at")
    search_fields = ("name", "clinic__name")
    autocomplete_fields = ("clinic",)
    list_select_related = ("clinic",)
    date_hierarchy = "created_at"
