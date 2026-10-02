import pytest
from django.core.exceptions import ValidationError

from apps.consents.models import Consent
from apps.consents.services import withdraw_consent

from .factories import ConsentDocumentFactory, ConsentFactory


@pytest.mark.django_db
class TestImmutability:
    def test_cannot_delete(self):
        consent = ConsentFactory()
        with pytest.raises(ValidationError):
            consent.delete()
        with pytest.raises(ValidationError):
            Consent.objects.all().delete()

    def test_cannot_edit_after_creation(self):
        consent = ConsentFactory()
        consent.document = ConsentDocumentFactory()
        with pytest.raises(ValidationError):
            consent.save()

    def test_withdrawal_is_recorded_once(self):
        consent = withdraw_consent(ConsentFactory())
        assert consent.withdrawn_at is not None
        consent.withdrawn_at = None
        with pytest.raises(ValidationError):
            consent.save()

    def test_published_document_is_frozen(self):
        document = ConsentDocumentFactory()
        document.text = "changed"
        with pytest.raises(ValidationError):
            document.save()


@pytest.mark.django_db
class TestConsentAPI:
    def test_grant_withdraw_and_regrant_keeps_history(self, participant_client, participant):
        document = ConsentDocumentFactory()

        granted = participant_client.post("/api/participant/consents/", {"document_id": str(document.pk)})
        assert granted.status_code == 201, granted.json()

        withdrawn = participant_client.post(f"/api/participant/consents/{granted.json()['id']}/withdraw/")
        assert withdrawn.json()["is_active"] is False

        participant_client.post("/api/participant/consents/", {"document_id": str(document.pk)})
        assert Consent.objects.filter(user=participant).count() == 2
        assert Consent.objects.filter(user=participant).active().count() == 1

    def test_no_delete_endpoint(self, participant_client, participant):
        consent = ConsentFactory(user=participant)
        assert participant_client.delete(f"/api/participant/consents/{consent.pk}/").status_code == 405

    def test_cannot_see_others_consents(self, participant_client):
        other = ConsentFactory()
        assert participant_client.get(f"/api/participant/consents/{other.pk}/").status_code == 404
