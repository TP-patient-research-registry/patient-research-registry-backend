from django.db import transaction
from django.utils import timezone

from .models import Consent, ConsentDocument, ConsentKind


def current_documents(language: str | None = None):
    """Latest published version of each consent kind (per language)."""
    qs = ConsentDocument.objects.filter(published_at__lte=timezone.now()).order_by("kind", "language", "-published_at")
    if language:
        qs = qs.filter(language=language)
    return qs.distinct("kind", "language")


@transaction.atomic
def grant_consent(user, document: ConsentDocument) -> Consent:
    existing = Consent.objects.active().filter(user=user, document=document).first()
    return existing or Consent.objects.create(user=user, document=document)


@transaction.atomic
def withdraw_consent(consent: Consent) -> Consent:
    if consent.withdrawn_at is None:
        consent.withdrawn_at = timezone.now()
        consent.save()
    return consent


def has_active_consent(user, kind: ConsentKind) -> bool:
    """True if the user currently holds a consent of `kind` (any published version)."""
    return Consent.objects.active().filter(user=user, document__kind=kind).exists()
