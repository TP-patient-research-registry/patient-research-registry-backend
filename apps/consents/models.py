from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class ConsentKind(models.TextChoices):
    # Explicit consent to processing of health data (GDPR art. 9(2)(a)).
    HEALTH_DATA_PROCESSING = "health_data_processing", _("Processing of health data")
    # Consent to be contacted about matching studies.
    STUDY_MATCHING_CONTACT = "study_matching_contact", _("Contact about matching studies")
    TERMS = "terms", _("Terms of use")


class ConsentDocument(BaseModel):
    """A versioned consent text. Once published it is frozen — publish a new version instead."""

    kind = models.CharField(max_length=40, choices=ConsentKind.choices)
    version = models.CharField(max_length=20)
    language = models.CharField(max_length=5, choices=settings.LANGUAGES, default="sk")
    title = models.CharField(max_length=255)
    text = models.TextField()
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=("kind", "version", "language"), name="unique_consent_doc_version")
        ]

    def __str__(self):
        return f"{self.get_kind_display()} v{self.version} ({self.language})"

    @property
    def is_published(self) -> bool:
        return self.published_at is not None and self.published_at <= timezone.now()

    def save(self, *args, **kwargs):
        if not self._state.adding:
            original = type(self).objects.get(pk=self.pk)
            if original.published_at is not None and (
                original.text != self.text or original.version != self.version or original.kind != self.kind
            ):
                raise ValidationError(_("A published consent document cannot be changed."))
        super().save(*args, **kwargs)


class ConsentQuerySet(models.QuerySet):
    def delete(self):
        raise ValidationError(_("Consent records are immutable and cannot be deleted."))

    def active(self):
        return self.filter(withdrawn_at__isnull=True)


class Consent(BaseModel):
    """
    Immutable consent history: rows are never deleted or edited. Withdrawal only sets
    `withdrawn_at`; granting again creates a new row.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="consents")
    document = models.ForeignKey(ConsentDocument, on_delete=models.PROTECT, related_name="consents")
    granted_at = models.DateTimeField(default=timezone.now)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    objects = ConsentQuerySet.as_manager()

    class Meta(BaseModel.Meta):
        ordering = ("-granted_at",)
        constraints = [
            # At most one active consent per user and document.
            models.UniqueConstraint(
                fields=("user", "document"),
                condition=models.Q(withdrawn_at__isnull=True),
                name="unique_active_consent",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.document}"

    @property
    def is_active(self) -> bool:
        return self.withdrawn_at is None

    def save(self, *args, **kwargs):
        if not self._state.adding:
            original = type(self).objects.get(pk=self.pk)
            changed = {
                f.attname
                for f in self._meta.concrete_fields
                if getattr(original, f.attname) != getattr(self, f.attname)
            } - {"updated_at"}
            if original.withdrawn_at is not None or changed - {"withdrawn_at"}:
                raise ValidationError(_("Consent records are immutable; only a withdrawal can be recorded."))
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(_("Consent records are immutable and cannot be deleted."))
