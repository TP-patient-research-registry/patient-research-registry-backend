from auditlog.signals import accessed
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.studies.models import Enrollment, EnrollmentStatus

from .models import Questionnaire, Response


def questionnaires_for_participant(user):
    enrolled_studies = Enrollment.objects.filter(participant=user, status=EnrollmentStatus.ENROLLED).values("study_id")
    return Questionnaire.objects.filter(study_id__in=enrolled_studies, is_active=True).select_related("study")


@transaction.atomic
def save_response(user, questionnaire: Questionnaire, data: dict, submit: bool) -> Response:
    if not questionnaires_for_participant(user).filter(pk=questionnaire.pk).exists():
        raise PermissionDenied("You are not enrolled in this study.")

    response, _ = Response.objects.select_for_update().get_or_create(questionnaire=questionnaire, participant=user)
    if response.submitted_at is not None:
        raise ValidationError("This questionnaire has already been submitted.")
    # TODO: validate `data` against the SurveyJS schema.
    response.data = data
    if submit:
        response.submitted_at = timezone.now()
    response.save()
    return response


def log_responses_access(responses) -> None:
    """Record researcher access to participants' answers (shown in the participant's access log)."""
    for response in responses:
        accessed.send(sender=Response, instance=response)
