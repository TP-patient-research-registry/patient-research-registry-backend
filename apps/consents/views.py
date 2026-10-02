from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsParticipant

from .models import Consent
from .permissions import IsConsentOwner
from .serializers import ConsentDocumentSerializer, ConsentSerializer
from .services import current_documents, grant_consent, withdraw_consent


class ConsentDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """Currently valid consent texts the participant can grant."""

    permission_classes = [IsParticipant]
    serializer_class = ConsentDocumentSerializer
    pagination_class = None

    def get_queryset(self):
        return current_documents(self.request.query_params.get("language"))


class ConsentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    """The participant's full consent history. No update/delete: withdraw via the action."""

    permission_classes = [IsParticipant, IsConsentOwner]
    serializer_class = ConsentSerializer

    def get_queryset(self):
        return Consent.objects.filter(user=self.request.user).select_related("document")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consent = grant_consent(request.user, serializer.validated_data["document"])
        return Response(self.get_serializer(consent).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=ConsentSerializer)
    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        consent = withdraw_consent(self.get_object())
        return Response(self.get_serializer(consent).data)
