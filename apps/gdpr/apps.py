from django.apps import AppConfig


class GdprConfig(AppConfig):
    name = "apps.gdpr"
    verbose_name = "GDPR"

    def ready(self):
        from auditlog.registry import auditlog

        from .models import DeletionRequest

        auditlog.register(DeletionRequest)
