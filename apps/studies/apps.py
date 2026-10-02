from django.apps import AppConfig


class StudiesConfig(AppConfig):
    name = "apps.studies"

    def ready(self):
        from auditlog.registry import auditlog

        from .models import EligibilityCriteria, Enrollment, Study

        auditlog.register(Study)
        auditlog.register(EligibilityCriteria)
        auditlog.register(Enrollment)
