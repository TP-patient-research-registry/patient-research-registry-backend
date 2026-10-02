from django.apps import AppConfig


class QuestionnairesConfig(AppConfig):
    name = "apps.questionnaires"

    def ready(self):
        from auditlog.registry import auditlog

        from .models import Questionnaire, Response

        auditlog.register(Questionnaire, exclude_fields=["schema"])
        auditlog.register(Response, mask_fields=["data"])
