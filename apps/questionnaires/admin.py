from django.contrib import admin

from .models import Questionnaire, Response


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ("title", "study", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "study__title")


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    """Answers (health data) are not displayed in the admin."""

    list_display = ("id", "questionnaire", "submitted_at")
    fields = ("questionnaire", "submitted_at", "created_at")
    readonly_fields = fields

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
