import pytest
from django.db import connection

from apps.accounts.models import ParticipantProfile, ResearcherProfile, Role, User


@pytest.mark.django_db
class TestSession:
    def test_anonymous(self, api_client):
        response = api_client.get("/api/auth/session")
        assert response.status_code == 200
        assert response.json() == {"is_authenticated": False, "user": None}
        assert "csrftoken" in response.cookies

    def test_authenticated(self, api_client, researcher):
        api_client.force_login(researcher)
        data = api_client.get("/api/auth/session/").json()
        assert data["is_authenticated"] is True
        assert data["user"] == {
            "id": str(researcher.pk),
            "email": researcher.email,
            "role": "researcher",
            "first_name": "",
            "last_name": "",
        }


@pytest.mark.django_db
class TestSignup:
    URL = "/api/auth/browser/v1/auth/signup"

    def test_signup_as_researcher_creates_unverified_profile(self, api_client):
        response = api_client.post(
            self.URL, {"email": "new@example.test", "password": "a-Strong-passw0rd!", "role": "researcher"}
        )
        assert response.status_code == 401  # pending email verification
        user = User.objects.get(email="new@example.test")
        assert user.role == Role.RESEARCHER
        assert ResearcherProfile.objects.get(user=user).is_verified is False

    def test_signup_cannot_self_assign_admin(self, api_client):
        api_client.post(self.URL, {"email": "evil@example.test", "password": "a-Strong-passw0rd!", "role": "admin"})
        assert not User.objects.filter(email="evil@example.test", role=Role.ADMIN).exists()


@pytest.mark.django_db
class TestParticipantProfile:
    def test_health_data_is_encrypted_at_rest(self, participant):
        with connection.cursor() as cursor:
            cursor.execute("SELECT diagnoses FROM accounts_participantprofile WHERE user_id = %s", [participant.pk])
            raw = bytes(cursor.fetchone()[0])
        assert b"E11" not in raw
        assert ParticipantProfile.objects.get(user=participant).diagnoses == ["E11.9"]

    def test_update_profile(self, participant_client):
        response = participant_client.patch(
            "/api/participant/profile/", {"region": "KE", "diagnoses": ["I10"]}, format="json"
        )
        assert response.status_code == 200, response.json()
        assert response.json()["region"] == "KE"

    def test_invalid_diagnosis_code(self, participant_client):
        response = participant_client.patch("/api/participant/profile/", {"diagnoses": ["diabetes"]}, format="json")
        assert response.status_code == 400
        assert "diagnoses" in response.json()["error"]["fields"]
