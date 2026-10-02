from apps.core.routers import UUIDRouter

from .views import ConsentDocumentViewSet, ConsentViewSet

participant_router = UUIDRouter()
participant_router.register("consent-documents", ConsentDocumentViewSet, basename="consent-document")
participant_router.register("consents", ConsentViewSet, basename="consent")

participant_patterns = participant_router.urls
