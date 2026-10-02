from django.urls import path

from apps.core.routers import UUIDRouter

from .views import (
    ParticipantEnrollmentViewSet,
    ParticipantStudyViewSet,
    PublicStudyViewSet,
    ResearcherParticipantViewSet,
    ResearcherStudyViewSet,
)

public_router = UUIDRouter()
public_router.register("studies", PublicStudyViewSet, basename="public-study")
public_patterns = public_router.urls

participant_router = UUIDRouter()
participant_router.register("studies", ParticipantStudyViewSet, basename="participant-study")
participant_router.register("enrollments", ParticipantEnrollmentViewSet, basename="participant-enrollment")
participant_patterns = participant_router.urls

researcher_router = UUIDRouter()
researcher_router.register("studies", ResearcherStudyViewSet, basename="researcher-study")
researcher_patterns = [
    *researcher_router.urls,
    path(
        "studies/<uuid:study_pk>/participants/",
        ResearcherParticipantViewSet.as_view({"get": "list"}),
        name="researcher-participant-list",
    ),
    path(
        "studies/<uuid:study_pk>/participants/<uuid:pseudonym>/",
        ResearcherParticipantViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="researcher-participant-detail",
    ),
]
