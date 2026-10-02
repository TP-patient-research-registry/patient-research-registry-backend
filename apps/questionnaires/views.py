from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response as APIResponse

from apps.core.permissions import IsParticipant, IsResearcher
from apps.studies.models import Enrollment
from apps.studies.views import StudyScopedMixin

from . import services
from .models import Response
from .serializers import ParticipantResponseSerializer, PseudonymizedResponseSerializer, QuestionnaireSerializer


class ParticipantQuestionnaireViewSet(viewsets.ReadOnlyModelViewSet):
    """Questionnaires of studies the participant is enrolled in."""

    permission_classes = [IsParticipant]
    serializer_class = QuestionnaireSerializer

    def get_queryset(self):
        return services.questionnaires_for_participant(self.request.user)

    @extend_schema(methods=["GET"], responses=ParticipantResponseSerializer)
    @extend_schema(methods=["PUT"], request=ParticipantResponseSerializer, responses=ParticipantResponseSerializer)
    @action(detail=True, methods=["get", "put"], serializer_class=ParticipantResponseSerializer)
    def response(self, request, pk=None):
        """GET the participant's draft/submitted answers; PUT to save a draft or submit (`submit: true`)."""
        questionnaire = self.get_object()
        if request.method == "GET":
            response = get_object_or_404(Response, questionnaire=questionnaire, participant=request.user)
            return APIResponse(ParticipantResponseSerializer(response).data)

        serializer = ParticipantResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = services.save_response(
            request.user, questionnaire, serializer.validated_data["data"], serializer.validated_data["submit"]
        )
        return APIResponse(ParticipantResponseSerializer(response).data)


class ResearcherQuestionnaireViewSet(StudyScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsResearcher]
    serializer_class = QuestionnaireSerializer

    def get_queryset(self):
        return self.get_study().questionnaires.all()

    def perform_create(self, serializer):
        serializer.save(study=self.get_study())

    @extend_schema(responses=PseudonymizedResponseSerializer(many=True))
    @action(detail=True, serializer_class=PseudonymizedResponseSerializer)
    def responses(self, request, study_pk=None, pk=None):
        """Submitted answers, pseudonymised. Every access is written to the audit log."""
        questionnaire = self.get_object()
        queryset = questionnaire.responses.filter(submitted_at__isnull=False).order_by("submitted_at")
        page = self.paginate_queryset(queryset)
        services.log_responses_access(page)
        pseudonyms = dict(
            Enrollment.objects.filter(study_id=questionnaire.study_id).values_list("participant_id", "pseudonym")
        )
        serializer = PseudonymizedResponseSerializer(page, many=True, context={"pseudonyms": pseudonyms})
        return self.get_paginated_response(serializer.data)
