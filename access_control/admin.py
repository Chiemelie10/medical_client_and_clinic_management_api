from django.contrib import admin

from .models import ClinicGroupPermission, ClinicUserGroup, ClinicUserPermission


class AccessAssignmentAdminMixin:
    readonly_fields = ("id", "created_at", "updated_at")
    list_filter = ("is_active", "clinic", "created_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50


@admin.register(ClinicGroupPermission)
class ClinicGroupPermissionAdmin(AccessAssignmentAdminMixin, admin.ModelAdmin):
    list_display = ("clinic", "group", "permission", "is_active", "created_at")
    search_fields = (
        "clinic__name",
        "group__name",
        "permission__name",
        "permission__codename",
    )
    autocomplete_fields = ("clinic", "group")
    list_select_related = ("clinic", "group", "permission")


@admin.register(ClinicUserGroup)
class ClinicUserGroupAdmin(AccessAssignmentAdminMixin, admin.ModelAdmin):
    list_display = ("clinic", "user", "group", "is_active", "created_at")
    search_fields = (
        "clinic__name",
        "user__email",
        "user__first_name",
        "user__last_name",
        "group__name",
    )
    autocomplete_fields = ("clinic", "user", "group")
    list_select_related = ("clinic", "user", "group")


@admin.register(ClinicUserPermission)
class ClinicUserPermissionAdmin(AccessAssignmentAdminMixin, admin.ModelAdmin):
    list_display = ("clinic", "user", "permission", "is_active", "created_at")
    search_fields = (
        "clinic__name",
        "user__email",
        "user__first_name",
        "user__last_name",
        "permission__name",
        "permission__codename",
    )
    autocomplete_fields = ("clinic", "user")
    list_select_related = ("clinic", "user", "permission")
