from clinics.models import ClinicMembership
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from typing import Iterable
from .models import (
    ClinicUserGroup,
    ClinicGroupPermission,
    ClinicUserPermission
)

class ClinicAccessService:
    @staticmethod
    def is_clinic_member(*, user_id: str, clinic_id: str) -> bool:
        """
        Checks if the user has an active membership in
        the specified clinic.
        """

        return ClinicMembership.objects.filter(
            user_id=user_id,
            clinic_id=clinic_id,
            is_active=True
        ).exists()
    
    @staticmethod
    def is_superuser(*, user_id: str) -> bool:
        """Checks id the user is a superuser."""

        User = get_user_model()

        return User.objects.filter(
            id=user_id,
            is_superuser=True
        ).exists()

    @staticmethod
    def get_group_ids(*, user_id: str, clinic_id: str) -> Iterable[int]:
        """
        Return the IDs of groups assigned to the user
        within the specified clinic.
        """
        ClinicUserGroup.objects.filter(
            user_id=user_id,
            clinic_id=clinic_id,
            is_active=True
        ).values_list(
            "group_id",
            flat=True
        )

    @classmethod
    def get_group_permission_ids(cls, *, user_id: str, clinic_id: str) -> set[int]:
        """
        Return permission IDs granted through the user's
        groups within the specified clinic.
        """
        group_ids = cls.get_group_ids(
            user_id=user_id,
            clinic_id=clinic_id
        )

        return set(
            ClinicGroupPermission.objects.filter(
                clinic_id=clinic_id,
                group_id__in=group_ids,
                is_active=True
            ).values_list(
                "permission_id",
                flat=True
            )
        )

    @staticmethod
    def get_direct_permission_ids(*, user_id: str, clinic_id: str) -> set[int]:
        """
        Return permission IDs granted directly to the user
        within the specified clinic.
        """
        return set(
            ClinicUserPermission.objects.filter(
                user_id=user_id,
                clinic_id=clinic_id,
                is_active=True
            ).values_list(
                "permission_id",
                flat=True
            )
        )

    @classmethod
    def get_effective_permission_ids(cls, *, user_id: str, clinic_id: str) -> set[int]:
        """
        Return all permission IDs the user effectively has
        within the specified clinic.

        Effective permissions =
        group permissions + direct user permissions.
        """

        if not cls.is_clinic_member(user_id=user_id, clinic_id=clinic_id):
            return set()

        group_permission_ids = cls.get_group_permission_ids(
            user_id=user_id,
            clinic_id=clinic_id
        )

        direct_permission_ids = cls.get_direct_permission_ids(
            user_id=user_id,
            clinic_id=clinic_id
        )

        return group_permission_ids | direct_permission_ids

    @classmethod
    def get_effective_permissions(cls, *, user_id: str, clinic_id: str):
        """
        Return a QuerySet of Django Permission objects
        available to the user within the clinic.
        """
        effective_permission_ids = cls.get_effective_permission_ids(
            user_id=user_id,
            clinic_id=clinic_id
        )

        return (
            Permission.objects
            .filter(id__in=effective_permission_ids)
            .select_related("content_type")
            .order_by(
                "content_type__app_label",
                "codename",
            )
        )

    @classmethod
    def has_permission(cls, *, user_id: str, clinic_id: str, permission: str) -> bool:
        """
        Check whether the user has a particular permission
        within the specified clinic.

        Example:
            appointments.view_appointment
            appointments.add_appointment
            appointments.change_appointment
            appointments.delete_appointment
        """

        try:
            app_label, codename = permission.split(".", 1)
        except ValueError:
            raise ValueError("Permission must use the format 'app_label.codename'.")
        
        if cls.is_superuser(user_id=user_id):
            return True

        if not cls.is_clinic_member(user_id=user_id, clinic_id=clinic_id):
            return False

        permission_ids = cls.get_effective_permission_ids(
            user_id=user_id,
            clinic_id=clinic_id
        )

        return Permission.objects.filter(
            id__in=permission_ids,
            content_type__app_lable=app_label,
            codename=codename
        ).exists()
