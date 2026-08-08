import uuid

from clinics.models import Clinic
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.db import models


class ClinicGroupPermission(models.Model):
    """This class defines what permissions a Group (Role) has within a specific Clinic."""
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="group_permissions")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="clinic_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clinic_group_permissions"
        ordering = ["-created_at"]
        verbose_name = "clinic group permission"
        verbose_name_plural = "clinic group permissions"

        constraints = [
            models.UniqueConstraint(
                fields=["clinic", "group", "permission"],
                name="clinic_group_permission_unique"
            )
        ]

    def __str__(self) -> str:
        return f"Clinic: {self.clinic.name} - Group: {self.group.name} - Permission: {self.permission.name}".strip()


class ClinicUserGroup(models.Model):
    """This class defines the Group (Role) a User holds within a specific clinic."""
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="user_groups")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="clinic_groups")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="clinic_users")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clinic_user_groups"
        ordering = ["-created_at"]
        verbose_name = "clinic user group"
        verbose_name_plural = "clinic user groups"

        constraints = [
            models.UniqueConstraint(
                fields=["clinic", "user", "group"],
                name="clinic_user_groups_unique"
            )
        ]

    def __str__(self) -> str:
        return f"Clinic: {self.clinic.name} - Group: {self.group.name} - User: {self.user.email}".strip()


class ClinicUserPermission(models.Model):
    """This class defines the permissions a User holds directly for a specific clinic."""
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="user_permissions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="clinic_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="clinic_users")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clinic_user_permissions"
        ordering = ["-created_at"]
        verbose_name = "clinic user permission"
        verbose_name_plural = "clinic user permissions"

        constraints = [
            models.UniqueConstraint(
                fields=["clinic", "user", "permission"],
                name="clinic_user_permissions_unique"
            )
        ]

    def __str__(self) -> str:
        return f"Clinic: {self.clinic.name} - Permission: {self.permission.name} - User: {self.user.email}".strip()
