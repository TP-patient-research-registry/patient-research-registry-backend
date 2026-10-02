from django.urls import path

from apps.core.routers import UUIDRouter

from .views import ParticipantQuestionnaireViewSet, ResearcherQuestionnaireViewSet

participant_router = UUIDRouter()
participant_router.register("questionnaires", ParticipantQuestionnaireViewSet, basename="participant-questionnaire")
participant_patterns = participant_router.urls

_list = ResearcherQuestionnaireViewSet.as_view({"get": "list", "post": "create"})
_detail = ResearcherQuestionnaireViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
_responses = ResearcherQuestionnaireViewSet.as_view({"get": "responses"})

researcher_patterns = [
    path("studies/<uuid:study_pk>/questionnaires/", _list, name="researcher-questionnaire-list"),
    path("studies/<uuid:study_pk>/questionnaires/<uuid:pk>/", _detail, name="researcher-questionnaire-detail"),
    path(
        "studies/<uuid:study_pk>/questionnaires/<uuid:pk>/responses/",
        _responses,
        name="researcher-questionnaire-responses",
    ),
]
