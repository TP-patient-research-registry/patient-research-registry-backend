import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Organization, Region
from apps.core.models import BaseModel


class StudyStatus(models.TextChoices):
    DRAFT = "draft", _("Draft")
    PUBLISHED = "published", _("Published")
    CLOSED = "closed", _("Closed")


class Study(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=StudyStatus.choices, default=StudyStatus.DRAFT)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_studies")
    organization = models.ForeignKey(
        Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name="studies"
    )
    results_summary = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        verbose_name_plural = "studies"

    def __str__(self):
        return self.title


class CriteriaSex(models.TextChoices):
    ANY = "any", _("Any")
    FEMALE = "female", _("Female")
    MALE = "male", _("Male")


class EligibilityCriteria(BaseModel):
    """Inclusion criteria used to recommend the study to matching participants."""

    study = models.OneToOneField(Study, on_delete=models.CASCADE, related_name="criteria")
    min_age = models.PositiveSmallIntegerField(null=True, blank=True)
    max_age = models.PositiveSmallIntegerField(null=True, blank=True)
    sex = models.CharField(max_length=10, choices=CriteriaSex.choices, default=CriteriaSex.ANY)
    # Empty list = no restriction.
    regions = ArrayField(models.CharField(max_length=2, choices=Region.choices), default=list, blank=True)
    # ICD-10 codes or prefixes ("E11" matches "E11.9"). Empty list = no restriction.
    diagnoses = ArrayField(models.CharField(max_length=10), default=list, blank=True)

    class Meta(BaseModel.Meta):
        verbose_name_plural = "eligibility criteria"

    def __str__(self):
        return f"Criteria for {self.study}"


class EnrollmentStatus(models.TextChoices):
    APPLIED = "applied", _("Applied")
    ENROLLED = "enrolled", _("Enrolled")
    WITHDRAWN = "withdrawn", _("Withdrawn")
    COMPLETED = "completed", _("Completed")


class Enrollment(BaseModel):
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.APPLIED)
    # Per-study pseudonym shown to researchers instead of any identity (not linkable across studies).
    pseudonym = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta(BaseModel.Meta):
        constraints = [models.UniqueConstraint(fields=("participant", "study"), name="unique_enrollment")]

    def __str__(self):
        return f"{self.pseudonym} in {self.study}"
