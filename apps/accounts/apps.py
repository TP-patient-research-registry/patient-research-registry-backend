from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "apps.accounts"

    def ready(self):
        from auditlog.registry import auditlog

        from .models import Organization, ParticipantProfile, ResearcherProfile, User

        auditlog.register(User, exclude_fields=["password", "last_login"])
        auditlog.register(ParticipantProfile, mask_fields=list(ParticipantProfile.ENCRYPTED_FIELDS))
        auditlog.register(ResearcherProfile)
        auditlog.register(Organization)
