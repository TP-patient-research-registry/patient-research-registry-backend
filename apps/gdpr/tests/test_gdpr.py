import json

import pytest

from apps.consents.tests.factories import ConsentFactory
from apps.studies.tests.factories import EnrollmentFactory


@pytest.mark.django_db
class TestDataExport:
    def test_export_contains_all_personal_data(self, participant_client, participant):
        ConsentFactory(user=participant)
        EnrollmentFactory(participant=participant)

        response = participant_client.get("/api/participant/my-data/export/")
        assert response.status_code == 200
        assert "attachment" in response["Content-Disposition"]
        data = json.loads(response.content)
        assert data["account"]["email"] == participant.email
        assert data["participant_profile"]["diagnoses"] == ["E11.9"]
        assert len(data["consents"]) == 1
        assert len(data["enrollments"]) == 1


@pytest.mark.django_db
class TestDeletionRequest:
    URL = "/api/participant/my-data/deletion-requests/"

    def test_only_one_open_request(self, participant_client):
        assert participant_client.post(self.URL, {"reason": "bye"}).status_code == 201
        assert participant_client.post(self.URL, {}).status_code == 400
        assert participant_client.get(self.URL).json()["count"] == 1


@pytest.mark.django_db
class TestAccessLog:
    def test_shows_own_changes_without_staff_identities(self, participant_client, participant):
        participant_client.patch("/api/participant/profile/", {"region": "KE"}, format="json")
        entries = participant_client.get("/api/participant/my-data/access-log/").json()["results"]
        assert entries, "expected audit entries for the participant's own data"
        assert {"timestamp", "action", "object_type", "actor"} <= set(entries[0])
        assert all("@" not in e["actor"] for e in entries)
