from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from .models import EligibilityCriteria, Enrollment, Study


class EligibilityCriteriaInline(admin.StackedInline):
    model = EligibilityCriteria
    can_delete = False


@admin.register(Study)
class StudyAdmin(GuardedModelAdmin):
    list_display = ("title", "status", "owner", "organization", "published_at")
    list_filter = ("status",)
    search_fields = ("title",)
    inlines = [EligibilityCriteriaInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("pseudonym", "study", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("pseudonym",)
