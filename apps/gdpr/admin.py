from django.contrib import admin

from .models import DeletionRequest


@admin.register(DeletionRequest)
class DeletionRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at", "processed_at")
    list_filter = ("status",)
    readonly_fields = ("user", "reason", "created_at")
    search_fields = ("user__email",)
