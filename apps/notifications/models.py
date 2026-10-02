from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class NotificationPreference(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preference"
    )
    email_matching_studies = models.BooleanField(default=True)
    email_study_updates = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification preferences of {self.user}"
