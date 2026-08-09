from django.contrib import admin

from .models import Country, State


class StateInline(admin.TabularInline):
    model = State
    fields = ("name",)
    extra = 0
    show_change_link = True


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 50
    inlines = (StateInline,)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "created_at", "updated_at")
    list_filter = ("country",)
    search_fields = ("name", "country__name")
    ordering = ("country__name", "name")
    autocomplete_fields = ("country",)
    list_select_related = ("country",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 50
