import pytest
from django.core import mail

from apps.accounts.tests.factories import ParticipantFactory, ResearcherFactory
from apps.consents.models import ConsentKind
from apps.consents.tests.factories import ConsentDocumentFactory, ConsentFactory
from apps.studies.models import Enrollment, EnrollmentStatus, StudyStatus

from .factories import EnrollmentFactory, PublishedStudyFactory, StudyFactory, set_criteria


@pytest.mark.django_db
class TestPublicStudies:
    def test_only_published_are_listed(self, api_client):
        published = PublishedStudyFactory()
        StudyFactory()  # draft
        results = api_client.get("/api/studies/").json()["results"]
        assert [s["id"] for s in results] == [str(published.pk)]
        assert "owner" not in results[0]

    def test_draft_detail_is_hidden(self, api_client):
        assert api_client.get(f"/api/studies/{StudyFactory().pk}/").status_code == 404


@pytest.mark.django_db
class TestResearcherStudies:
    def test_create_assigns_object_permissions(self, researcher_client, researcher):
        response = researcher_client.post("/api/researcher/studies/", {"title": "T", "description": "D"})
        assert response.status_code == 201, response.json()
        study_id = response.json()["id"]
        assert researcher_client.get(f"/api/researcher/studies/{study_id}/").status_code == 200

    def test_cannot_access_other_researchers_study(self, researcher_client):
        other = StudyFactory()
        assert researcher_client.get(f"/api/researcher/studies/{other.pk}/").status_code == 404
        assert researcher_client.get(f"/api/researcher/studies/{other.pk}/participants/").status_code == 404

    def test_unverified_researcher_cannot_publish(self, api_client):
        researcher = ResearcherFactory(profile__is_verified=False)
        study = StudyFactory(owner=researcher)
        api_client.force_login(researcher)
        assert api_client.post(f"/api/researcher/studies/{study.pk}/publish/").status_code == 403

    def test_update_criteria(self, researcher_client, researcher):
        study = StudyFactory(owner=researcher)
        response = researcher_client.put(
            f"/api/researcher/studies/{study.pk}/criteria/",
            {"min_age": 18, "max_age": 65, "sex": "any", "regions": ["BA"], "diagnoses": ["E11"]},
            format="json",
        )
        assert response.status_code == 200, response.json()
        study.criteria.refresh_from_db()
        assert study.criteria.regions == ["BA"]

    def test_participants_are_pseudonymized(self, researcher_client, researcher):
        enrollment = EnrollmentFactory(study=PublishedStudyFactory(owner=researcher))
        response = researcher_client.get(f"/api/researcher/studies/{enrollment.study_id}/participants/")
        body = response.content.decode()
        assert response.json()["results"][0]["participant_id"] == str(enrollment.pseudonym)
        assert enrollment.participant.email not in body
        assert str(enrollment.participant.pk) not in body

    def test_accept_participant(self, researcher_client, researcher):
        enrollment = EnrollmentFactory(study=PublishedStudyFactory(owner=researcher))
        url = f"/api/researcher/studies/{enrollment.study_id}/participants/{enrollment.pseudonym}/"
        assert researcher_client.patch(url, {"status": "enrolled"}).status_code == 200
        enrollment.refresh_from_db()
        assert enrollment.status == EnrollmentStatus.ENROLLED
        assert researcher_client.patch(url, {"status": "applied"}).status_code == 400


@pytest.mark.django_db
class TestPublishNotifications:
    def test_publish_emails_matching_consenting_participants_without_health_data(
        self, researcher_client, researcher, django_capture_on_commit_callbacks
    ):
        study = StudyFactory(owner=researcher, title="Diabetes E11 trial")
        set_criteria(study, diagnoses=["E11"])
        contact_doc = ConsentDocumentFactory(kind=ConsentKind.STUDY_MATCHING_CONTACT)

        matching = ParticipantFactory()  # default profile has E11.9
        ConsentFactory(user=matching, document=contact_doc)
        ParticipantFactory()  # matches, but no contact consent
        non_matching = ParticipantFactory(profile__diagnoses=["J45"])
        ConsentFactory(user=non_matching, document=contact_doc)

        with django_capture_on_commit_callbacks(execute=True):
            response = researcher_client.post(f"/api/researcher/studies/{study.pk}/publish/")
        assert response.status_code == 200, response.json()
        assert response.json()["status"] == StudyStatus.PUBLISHED

        assert [m.to for m in mail.outbox] == [[matching.email]]
        email = mail.outbox[0]
        for leaked in ("Diabetes", "E11", study.title):
            assert leaked not in email.subject + email.body


@pytest.mark.django_db
class TestParticipantStudies:
    def test_apply_requires_health_data_consent(self, participant_client, participant):
        study = PublishedStudyFactory()
        assert participant_client.post(f"/api/participant/studies/{study.pk}/apply/").status_code == 400

        ConsentFactory(user=participant)  # health data processing consent
        response = participant_client.post(f"/api/participant/studies/{study.pk}/apply/")
        assert response.status_code == 201, response.json()
        assert Enrollment.objects.filter(participant=participant, study=study).exists()

    def test_recommended(self, participant_client, participant):
        matching = PublishedStudyFactory()
        set_criteria(matching, diagnoses=["E11"])
        other = PublishedStudyFactory()
        set_criteria(other, diagnoses=["I10"])

        results = participant_client.get("/api/participant/studies/recommended/").json()["results"]
        assert [s["id"] for s in results] == [str(matching.pk)]

    def test_withdraw_enrollment(self, participant_client, participant):
        enrollment = EnrollmentFactory(participant=participant)
        response = participant_client.post(f"/api/participant/enrollments/{enrollment.pk}/withdraw/")
        assert response.json()["status"] == EnrollmentStatus.WITHDRAWN
