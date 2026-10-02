import pytest

from apps.consents.models import ConsentKind
from apps.consents.tests.factories import ConsentDocumentFactory, ConsentFactory
from apps.notifications.models import NotificationPreference
from apps.notifications.services import matching_participants
from apps.studies.tests.factories import PublishedStudyFactory


@pytest.mark.django_db
def test_opted_out_participants_are_not_notified(participant):
    ConsentFactory(user=participant, document=ConsentDocumentFactory(kind=ConsentKind.STUDY_MATCHING_CONTACT))
    study = PublishedStudyFactory()
    assert matching_participants(study) == [participant]

    NotificationPreference.objects.create(user=participant, email_matching_studies=False)
    assert matching_participants(study) == []


@pytest.mark.django_db
def test_update_preferences(participant_client):
    response = participant_client.patch("/api/participant/notification-preferences/", {"email_matching_studies": False})
    assert response.status_code == 200
    assert response.json()["email_matching_studies"] is False
