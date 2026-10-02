from django.urls import path

from .views import NotificationPreferenceView

participant_patterns = [
    path(
        "notification-preferences/",
        NotificationPreferenceView.as_view(),
        name="participant-notification-preferences",
    )
]
