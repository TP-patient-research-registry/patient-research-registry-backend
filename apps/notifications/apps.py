from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "apps.notifications"

    def ready(self):
        from auditlog.registry import auditlog

        from .models import NotificationPreference

        auditlog.register(NotificationPreference)
