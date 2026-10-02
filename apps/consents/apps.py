from django.apps import AppConfig


class ConsentsConfig(AppConfig):
    name = "apps.consents"

    def ready(self):
        from auditlog.registry import auditlog

        from .models import Consent, ConsentDocument

        auditlog.register(ConsentDocument, exclude_fields=["text"])
        auditlog.register(Consent)
