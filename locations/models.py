from django.db import models


class Country(models.Model):
    """The class defines the attributes of the Country model."""
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "countries"
        ordering = ["name"]
        verbose_name = "country"
        verbose_name_plural = "countries"

    def __str__(self) -> str:
        return self.name


class State(models.Model):
    """The class defines the attributes of the State model."""
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")

    class Meta:
        db_table = "states"
        ordering = ["name"]
        verbose_name = "state"
        verbose_name_plural = "states"

        constraints = [
            models.UniqueConstraint(
                fields=["country", "name"],
                name="states_country_name_unique"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name}, {self.country.name}"
