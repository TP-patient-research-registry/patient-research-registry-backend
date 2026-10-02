from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Organization, ParticipantProfile, ResearcherProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password", "role")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "role", "password1", "password2")}),)


@admin.register(ResearcherProfile)
class ResearcherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "institution", "organization", "is_verified")
    list_filter = ("is_verified",)
    search_fields = ("user__email", "institution")
    autocomplete_fields = ("user", "organization")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "registration_number", "is_verified")
    list_filter = ("is_verified",)
    search_fields = ("name", "registration_number")


@admin.register(ParticipantProfile)
class ParticipantProfileAdmin(admin.ModelAdmin):
    """Health data is intentionally not shown in the admin (data minimisation)."""

    list_display = ("id", "user", "created_at")
    fields = ("user", "created_at", "updated_at")
    readonly_fields = fields
    search_fields = ("user__email",)

    def has_add_permission(self, request):
        return False
