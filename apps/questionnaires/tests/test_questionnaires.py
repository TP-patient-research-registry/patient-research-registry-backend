import pytest
from auditlog.models import LogEntry

from apps.questionnaires.models import Response
from apps.studies.models import EnrollmentStatus
from apps.studies.tests.factories import EnrollmentFactory, PublishedStudyFactory

from .factories import QuestionnaireFactory


@pytest.fixture
def enrolled(participant):
    return EnrollmentFactory(participant=participant, status=EnrollmentStatus.ENROLLED)


@pytest.mark.django_db
class TestParticipantQuestionnaires:
    def test_only_enrolled_studies_are_visible(self, participant_client, enrolled):
        mine = QuestionnaireFactory(study=enrolled.study)
        QuestionnaireFactory()
        results = participant_client.get("/api/participant/questionnaires/").json()["results"]
        assert [q["id"] for q in results] == [str(mine.pk)]

    def test_save_draft_then_submit_then_locked(self, participant_client, enrolled):
        questionnaire = QuestionnaireFactory(study=enrolled.study)
        url = f"/api/participant/questionnaires/{questionnaire.pk}/response/"

        draft = participant_client.put(url, {"data": {"q1": "a"}}, format="json")
        assert draft.status_code == 200, draft.json()
        assert draft.json()["submitted_at"] is None

        submitted = participant_client.put(url, {"data": {"q1": "b"}, "submit": True}, format="json")
        assert submitted.json()["submitted_at"] is not None

        assert participant_client.put(url, {"data": {"q1": "c"}}, format="json").status_code == 400
        assert participant_client.get(url).json()["data"] == {"q1": "b"}


@pytest.mark.django_db
class TestResearcherResponses:
    def test_responses_are_pseudonymized_and_access_is_logged(self, researcher_client, researcher, participant):
        enrollment = EnrollmentFactory(
            participant=participant, study=PublishedStudyFactory(owner=researcher), status=EnrollmentStatus.ENROLLED
        )
        questionnaire = QuestionnaireFactory(study=enrollment.study)
        response = Response.objects.create(
            questionnaire=questionnaire, participant=participant, data={"q1": "x"}, submitted_at="2026-01-01T00:00Z"
        )

        url = f"/api/researcher/studies/{enrollment.study_id}/questionnaires/{questionnaire.pk}/responses/"
        api_response = researcher_client.get(url)
        assert api_response.status_code == 200
        assert api_response.json()["results"][0]["participant_id"] == str(enrollment.pseudonym)
        assert participant.email not in api_response.content.decode()

        assert LogEntry.objects.filter(
            object_pk=str(response.pk), action=LogEntry.Action.ACCESS, actor=researcher
        ).exists()
