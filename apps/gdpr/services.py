from auditlog.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.models import ParticipantProfile
from apps.consents.models import Consent
from apps.notifications.models import NotificationPreference
from apps.questionnaires.models import Response
from apps.studies.models import Enrollment

from .models import DeletionRequest, DeletionRequestStatus


def export_user_data(user) -> dict:
    """All personal data we hold about `user` (GDPR art. 15 & 20), as JSON-serialisable dict."""
    profile = ParticipantProfile.objects.filter(user=user).first()
    preference = NotificationPreference.objects.filter(user=user).first()

    return {
        "exported_at": timezone.now().isoformat(),
        "account": {
            "id": str(user.pk),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "date_joined": user.date_joined.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
        },
        "participant_profile": profile
        and {
            "birth_year": profile.birth_year,
            "sex": profile.sex,
            "region": profile.region,
            "diagnoses": profile.diagnoses,
            "updated_at": profile.updated_at.isoformat(),
        },
        "consents": [
            {
                "document": str(c.document),
                "document_id": str(c.document_id),
                "granted_at": c.granted_at.isoformat(),
                "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
            }
            for c in Consent.objects.filter(user=user).select_related("document")
        ],
        "enrollments": [
            {
                "study_id": str(e.study_id),
                "study_title": e.study.title,
                "status": e.status,
                "pseudonym": str(e.pseudonym),
                "created_at": e.created_at.isoformat(),
            }
            for e in Enrollment.objects.filter(participant=user).select_related("study")
        ],
        "questionnaire_responses": [
            {
                "questionnaire_id": str(r.questionnaire_id),
                "questionnaire_title": r.questionnaire.title,
                "data": r.data,
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            }
            for r in Response.objects.filter(participant=user).select_related("questionnaire")
        ],
        "notification_preferences": preference
        and {
            "email_matching_studies": preference.email_matching_studies,
            "email_study_updates": preference.email_study_updates,
        },
        "deletion_requests": [
            {"status": d.status, "created_at": d.created_at.isoformat()}
            for d in DeletionRequest.objects.filter(user=user)
        ],
    }


def request_deletion(user, reason: str = "") -> DeletionRequest:
    open_statuses = (DeletionRequestStatus.PENDING, DeletionRequestStatus.PROCESSING)
    if DeletionRequest.objects.filter(user=user, status__in=open_statuses).exists():
        raise ValidationError("A deletion request is already being processed.")
    # TODO: notify administrators; processing workflow (anonymisation) is done in the admin.
    return DeletionRequest.objects.create(user=user, reason=reason)


def access_log_for(user):
    """Audit log entries (create/update/delete/access) about objects that belong to `user`."""
    owned = [
        (get_user_model(), [user.pk]),
        (ParticipantProfile, ParticipantProfile.objects.filter(user=user).values_list("pk", flat=True)),
        (Consent, Consent.objects.filter(user=user).values_list("pk", flat=True)),
        (Enrollment, Enrollment.objects.filter(participant=user).values_list("pk", flat=True)),
        (Response, Response.objects.filter(participant=user).values_list("pk", flat=True)),
    ]
    condition = Q(pk__in=[])
    for model, pks in owned:
        content_type = ContentType.objects.get_for_model(model)
        condition |= Q(content_type=content_type, object_pk__in=[str(pk) for pk in pks])

    return LogEntry.objects.filter(condition).select_related("actor", "content_type").order_by("-timestamp")
