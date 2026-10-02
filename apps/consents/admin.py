from django.contrib import admin

from .models import Consent, ConsentDocument


@admin.register(ConsentDocument)
class ConsentDocumentAdmin(admin.ModelAdmin):
    list_display = ("kind", "version", "language", "published_at")
    list_filter = ("kind", "language")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.published_at:
            return ("kind", "version", "language", "title", "text", "published_at")
        return ()


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    """Read-only: consent history is never edited by hand."""

    list_display = ("id", "user", "document", "granted_at", "withdrawn_at")
    list_filter = ("document__kind",)
    search_fields = ("user__email",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
