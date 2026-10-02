import json

from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsParticipant

from . import services
from .models import DeletionRequest
from .serializers import AccessLogEntrySerializer, DeletionRequestSerializer


class DataExportView(APIView):
    """Download all personal data as JSON (GDPR art. 15 & 20)."""

    permission_classes = [IsParticipant]

    @extend_schema(responses={(200, "application/json"): OpenApiTypes.OBJECT})
    def get(self, request):
        data = services.export_user_data(request.user)
        filename = f"my-data-{timezone.localdate().isoformat()}.json"
        response = HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2), content_type="application/json; charset=utf-8"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "no-store"
        return response


class DeletionRequestViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Request erasure of the account and data (GDPR art. 17)."""

    permission_classes = [IsParticipant]
    serializer_class = DeletionRequestSerializer

    def get_queryset(self):
        return DeletionRequest.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deletion_request = services.request_deletion(request.user, serializer.validated_data.get("reason", ""))
        return Response(self.get_serializer(deletion_request).data, status=status.HTTP_201_CREATED)


class AccessLogView(generics.ListAPIView):
    """Who did what with the participant's data (based on django-auditlog)."""

    permission_classes = [IsParticipant]
    serializer_class = AccessLogEntrySerializer

    def get_queryset(self):
        return services.access_log_for(self.request.user)
