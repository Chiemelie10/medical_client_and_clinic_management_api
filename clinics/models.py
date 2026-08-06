import zoneinfo
import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from locations.models import Country, State


class Clinic(models.Model):
    """
    The class defines the attributes of the Clinic model.
    Each object of this class represents a tenancy in the application
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    contact_phone_number = models.CharField(max_length=20, null=True, blank=True)
    contact_email = models.EmailField(unique=True, null=True, blank=True)
    address = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="clinics/logos", null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="clinics")
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="clinics")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="clinics_owned")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through="ClinicMembership", related_name="clinics_joined")

    class Meta:
        db_table = "clinics"
        ordering = ["-created_at"]
        verbose_name = "clinic"
        verbose_name_plural = "clinics"

    def __str__(self) -> str:
        return self.name.strip()


class ClinicMembership(models.Model):
    """
    The class defines the attributes of the ClinicMembership model.
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    specializations = ArrayField(
        models.CharField(max_length=255),
        blank=True,
        default=list
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clinic_memberships"
        ordering = ["-created_at"]
        verbose_name = "clinic membership"
        verbose_name_plural = "clinic memberships"

        constraints = [
            models.UniqueConstraint(
                fields=["clinic", "user"],
                name="clinic_memberships_clinic_user_unique"
            )
        ]

        indexes = [
            GinIndex(
                fields=["specializations"],
                name="membership_spec_gin_idx"
            )
        ]

    def __str__(self) -> str:
        return f"{self.clinic.name} {self.user.email}"


class ClinicSetting(models.Model):
    """
    The class defines the attributes of the ClinicSetting model.
    """
    TIMEZONE_CHOICES = [(tz, tz) for tz in sorted(zoneinfo.available_timezones())]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    clinic = models.OneToOneField(Clinic, on_delete=models.CASCADE, related_name="setting")
    timezone = models.CharField(max_length=63, choices=TIMEZONE_CHOICES, default="UTC")
    appointment_duration = models.IntegerField(default=30)
    allow_public_booking = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = "clinic_settings"
        ordering = ["-created_at"]
        verbose_name = "clinic setting"
        verbose_name_plural = "clinic settings"

    def __str__(self) -> str:
        return f"Setting for {self.clinic.name}"
    

class ClinicWorkingDay(models.Model):
    """The class defines the attributes of the ClinicWorkingDay model."""

    DAY_CHOICES = [
        (1, "Sunday"),
        (2, "Monday"),
        (3, "Tuesday"),
        (4, "Wednesday"),
        (5, "Thursday"),
        (6, "Friday"),
        (7, "Saturday")
    ]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    clinic_setting = models.ForeignKey(ClinicSetting, on_delete=models.CASCADE, related_name="working_days")
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    open_time = models.TimeField(default="08:00:00")
    close_time = models.TimeField(default="17:00:00")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clinic_working_days"
        ordering = ["-created_at"]
        verbose_name = "clinic working day"
        verbose_name_plural = "clinic working days"

        constraints = [
            models.UniqueConstraint(
                fields=["clinic_setting", "day_of_week"],
                name="unique_clinic_day"
            )
        ]

    def __str__(self) -> str:
        return f"Working days setting for {self.clinic_setting.clinic.name}"


class ClinicInvitation(models.Model):
    """
    The class defines the attributes of the ClinicInvitation model.
    """
    INVITATION_STATUS = [
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("pending", "Pending")
    ]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="clinic_invitation_made")
    status = models.CharField(max_length=20, choices=INVITATION_STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = "clinic_invitations"
        ordering = ["-created_at"]
        verbose_name = "clinic invitation"
        verbose_name_plural = "clinic invitations"

        constraints = [
            models.UniqueConstraint(
                fields=["clinic", "email"],
                name="clinic_invitations_email_unique"
            )
        ]

    def __str__(self) -> str:
        return f"Invitaion from {self.clinic.name} to {self.email}"


class ClinicService(models.Model):
    """
    The class defines the attributes of the ClinicService model.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=255)
    service_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clinic_services"
        ordering = ["-created_at"]
        verbose_name = "clinic service"
        verbose_name_plural = "clinic services"

        constraints = [
            models.UniqueConstraint(
                fields=["clinic", "name"],
                name="clinic_services_name_unique"
            )
        ]

    def __str__(self) -> str:
        return f"{self.clinic.name} {self.name}"
