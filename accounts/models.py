import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager

class User(AbstractUser):
    """The custom user model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    thumbnail = models.ImageField(upload_to="users/thumbnails/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]
        verbose_name = "user"
        verbose_name_plural = "users"

        indexes = [
            models.Index(
                fields=["is_active", "-date_joined"],
                name="users_active_joined_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:

        if not self.first_name and not self.last_name:
            return ""

        return f"{self.first_name} {self.last_name}".strip()
