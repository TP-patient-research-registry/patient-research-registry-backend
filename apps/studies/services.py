from datetime import date

from django.db import transaction
from django.utils import timezone
from guardian.shortcuts import assign_perm
from rest_framework.exceptions import ValidationError

from apps.accounts.models import ParticipantProfile
from apps.consents.models import ConsentKind
from apps.consents.services import has_active_consent

from .models import EligibilityCriteria, Enrollment, EnrollmentStatus, Study, StudyStatus

OWNER_PERMISSIONS = ("view_study", "change_study", "delete_study")


@transaction.atomic
def create_study(owner, **data) -> Study:
    study = Study.objects.create(owner=owner, **data)
    EligibilityCriteria.objects.create(study=study)
    for perm in OWNER_PERMISSIONS:
        assign_perm(f"studies.{perm}", owner, study)
    # TODO: share with organization members (guardian group per Organization).
    return study


@transaction.atomic
def publish_study(study: Study) -> Study:
    if study.status != StudyStatus.DRAFT:
        raise ValidationError("Only draft studies can be published.")
    study.status = StudyStatus.PUBLISHED
    study.published_at = timezone.now()
    study.save(update_fields=["status", "published_at", "updated_at"])

    from apps.notifications.tasks import notify_matching_participants

    transaction.on_commit(lambda: notify_matching_participants.delay(str(study.pk)))
    return study


def close_study(study: Study) -> Study:
    if study.status != StudyStatus.PUBLISHED:
        raise ValidationError("Only published studies can be closed.")
    study.status = StudyStatus.CLOSED
    study.save(update_fields=["status", "updated_at"])
    return study


def profile_matches(criteria: EligibilityCriteria, profile: ParticipantProfile, today: date | None = None) -> bool:
    """Pure eligibility check. Runs in Python because profile health fields are encrypted."""
    today = today or timezone.localdate()

    if criteria.min_age is not None or criteria.max_age is not None:
        if not profile.birth_year:
            return False
        age = today.year - profile.birth_year  # approximate: only the birth year is stored
        if criteria.min_age is not None and age < criteria.min_age:
            return False
        if criteria.max_age is not None and age > criteria.max_age:
            return False

    if criteria.sex != "any" and profile.sex != criteria.sex:
        return False

    if criteria.regions and profile.region not in criteria.regions:
        return False

    if criteria.diagnoses:
        codes = profile.diagnoses or []
        if not any(code.startswith(prefix) for code in codes for prefix in criteria.diagnoses):
            return False

    return True


def recommended_studies(user):
    profile = ParticipantProfile.objects.filter(user=user).first()
    if profile is None:
        return []
    enrolled = Enrollment.objects.filter(participant=user).values("study_id")
    candidates = (
        Study.objects.filter(status=StudyStatus.PUBLISHED, criteria__isnull=False)
        .exclude(pk__in=enrolled)
        .select_related("criteria", "organization")
    )
    return [study for study in candidates if profile_matches(study.criteria, profile)]


@transaction.atomic
def apply_to_study(user, study: Study) -> Enrollment:
    if study.status != StudyStatus.PUBLISHED:
        raise ValidationError("This study is not accepting participants.")
    if not has_active_consent(user, ConsentKind.HEALTH_DATA_PROCESSING):
        raise ValidationError("Consent to processing of health data is required to join a study.")

    enrollment, created = Enrollment.objects.select_for_update().get_or_create(participant=user, study=study)
    if not created:
        if enrollment.status != EnrollmentStatus.WITHDRAWN:
            raise ValidationError("You have already applied to this study.")
        enrollment.status = EnrollmentStatus.APPLIED
        enrollment.save(update_fields=["status", "updated_at"])
    return enrollment


def withdraw_enrollment(enrollment: Enrollment) -> Enrollment:
    if enrollment.status in (EnrollmentStatus.WITHDRAWN, EnrollmentStatus.COMPLETED):
        raise ValidationError("This enrollment can no longer be withdrawn.")
    enrollment.status = EnrollmentStatus.WITHDRAWN
    enrollment.save(update_fields=["status", "updated_at"])
    return enrollment


# Status changes a researcher may make: current → allowed targets.
RESEARCHER_TRANSITIONS = {
    EnrollmentStatus.APPLIED: {EnrollmentStatus.ENROLLED, EnrollmentStatus.WITHDRAWN},
    EnrollmentStatus.ENROLLED: {EnrollmentStatus.COMPLETED, EnrollmentStatus.WITHDRAWN},
}


def change_enrollment_status(enrollment: Enrollment, status: str) -> Enrollment:
    if status not in RESEARCHER_TRANSITIONS.get(enrollment.status, set()):
        raise ValidationError({"status": f"Cannot change status from {enrollment.status} to {status}."})
    enrollment.status = status
    enrollment.save(update_fields=["status", "updated_at"])
    return enrollment
