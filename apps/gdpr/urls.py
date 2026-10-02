from django.urls import path

from apps.core.routers import UUIDRouter

from .views import AccessLogView, DataExportView, DeletionRequestViewSet

router = UUIDRouter()
router.register("my-data/deletion-requests", DeletionRequestViewSet, basename="deletion-request")

participant_patterns = [
    path("my-data/export/", DataExportView.as_view(), name="my-data-export"),
    path("my-data/access-log/", AccessLogView.as_view(), name="my-data-access-log"),
    *router.urls,
]
