from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class DeletionRequestStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    PROCESSING = "processing", _("Processing")
    COMPLETED = "completed", _("Completed")
    REJECTED = "rejected", _("Rejected")


class DeletionRequest(BaseModel):
    """
    Right to erasure (GDPR art. 17). Processed by an administrator: data that must be retained
    (e.g. consent proofs, data already used in studies) is anonymised instead of deleted.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="deletion_requests"
    )
    status = models.CharField(
        max_length=20, choices=DeletionRequestStatus.choices, default=DeletionRequestStatus.PENDING
    )
    reason = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)

    def __str__(self):
        return f"Deletion request {self.pk} ({self.status})"
