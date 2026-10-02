from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.permissions import IsVerifiedResearcher
from apps.core.permissions import IsParticipant, IsResearcher

from . import services
from .models import Enrollment, Study, StudyStatus
from .permissions import StudyObjectPermission
from .serializers import (
    EligibilityCriteriaSerializer,
    EnrollmentSerializer,
    PseudonymizedEnrollmentSerializer,
    PublicStudySerializer,
    ResearcherStudySerializer,
)


def published_studies():
    return Study.objects.filter(status=StudyStatus.PUBLISHED).select_related("organization", "criteria")


def studies_for_researcher(user, perm: str = "studies.view_study"):
    return get_objects_for_user(user, perm, klass=Study, accept_global_perms=False)


# --- Public -----------------------------------------------------------------------------------


class PublicStudyViewSet(viewsets.ReadOnlyModelViewSet):
    """Published studies, visible to everyone."""

    permission_classes = [AllowAny]
    serializer_class = PublicStudySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "description"]

    def get_queryset(self):
        return published_studies()


# --- Participant ------------------------------------------------------------------------------


class ParticipantStudyViewSet(viewsets.ReadOnlyModelViewSet):
    """Search published studies, get recommendations and apply."""

    permission_classes = [IsParticipant]
    serializer_class = PublicStudySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "description"]

    def get_queryset(self):
        return published_studies()

    @extend_schema(responses=PublicStudySerializer(many=True))
    @action(detail=False)
    def recommended(self, request):
        studies = services.recommended_studies(request.user)
        page = self.paginate_queryset(studies)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    @extend_schema(request=None, responses={201: EnrollmentSerializer})
    @action(detail=True, methods=["post"])
    def apply(self, request, pk=None):
        enrollment = services.apply_to_study(request.user, self.get_object())
        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)


class ParticipantEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsParticipant]
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        return Enrollment.objects.filter(participant=self.request.user).select_related(
            "study__organization", "study__criteria"
        )

    @extend_schema(request=None, responses=EnrollmentSerializer)
    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        enrollment = services.withdraw_enrollment(self.get_object())
        return Response(self.get_serializer(enrollment).data)


# --- Researcher -------------------------------------------------------------------------------


class ResearcherStudyViewSet(viewsets.ModelViewSet):
    """Studies the researcher has object permissions for (django-guardian)."""

    permission_classes = [IsResearcher, StudyObjectPermission]
    serializer_class = ResearcherStudySerializer

    def get_queryset(self):
        return (
            studies_for_researcher(self.request.user)
            .select_related("criteria", "organization")
            .prefetch_related(Prefetch("enrollments", queryset=Enrollment.objects.only("id", "study_id")))
        )

    def perform_create(self, serializer):
        serializer.instance = services.create_study(self.request.user, **serializer.validated_data)

    def perform_destroy(self, instance):
        if instance.status != StudyStatus.DRAFT:
            raise ValidationError("Only draft studies can be deleted; close the study instead.")
        instance.delete()

    @extend_schema(request=None, responses=ResearcherStudySerializer)
    @action(
        detail=True, methods=["post"], permission_classes=[IsResearcher, IsVerifiedResearcher, StudyObjectPermission]
    )
    def publish(self, request, pk=None):
        study = services.publish_study(self.get_object())
        return Response(self.get_serializer(study).data)

    @extend_schema(request=None, responses=ResearcherStudySerializer)
    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        study = services.close_study(self.get_object())
        return Response(self.get_serializer(study).data)

    @extend_schema(methods=["GET"], responses=EligibilityCriteriaSerializer)
    @extend_schema(methods=["PUT"], request=EligibilityCriteriaSerializer, responses=EligibilityCriteriaSerializer)
    @action(detail=True, methods=["get", "put"], serializer_class=EligibilityCriteriaSerializer)
    def criteria(self, request, pk=None):
        criteria = self.get_object().criteria
        if request.method == "GET":
            return Response(EligibilityCriteriaSerializer(criteria).data)
        serializer = EligibilityCriteriaSerializer(criteria, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StudyScopedMixin:
    """For views nested under /researcher/studies/<study_pk>/: resolves the study + checks perms."""

    def get_study(self, perm: str | None = None) -> Study:
        if not hasattr(self, "_study"):
            if perm is None:
                perm = (
                    "studies.view_study"
                    if self.request.method in ("GET", "HEAD", "OPTIONS")
                    else "studies.change_study"
                )
            self._study = get_object_or_404(studies_for_researcher(self.request.user, perm), pk=self.kwargs["study_pk"])
        return self._study


class ResearcherParticipantViewSet(
    StudyScopedMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """Pseudonymised participants of a study. Researchers can only change the enrollment status."""

    permission_classes = [IsResearcher]
    serializer_class = PseudonymizedEnrollmentSerializer
    lookup_field = "pseudonym"
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return Enrollment.objects.filter(study=self.get_study()).order_by("created_at")

    def perform_update(self, serializer):
        services.change_enrollment_status(serializer.instance, serializer.validated_data["status"])
