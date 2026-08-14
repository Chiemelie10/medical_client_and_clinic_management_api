from rest_framework import serializers
from .models import Clinic


class UserClinicSerializer(serializers.ModelSerializer):
    """
    This class defines fields of the Clinic the model to be
    retrieved when querying to get authenticated user.
    """
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Clinic
        fields = [
            "id",
            "name",
            "roles",
        ]

    def get_roles(self, obj) -> list[str]:
        """
        This method returns the roles of a user for specific clinics
        already prefetched in the me method of auth_service class.
        """
        user_clinic_groups = getattr(obj, "user_roles_at_clinic", [])
        return [user_clinic_group.group.name for user_clinic_group in user_clinic_groups]
