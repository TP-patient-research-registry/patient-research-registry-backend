from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.utils import translation
from django.utils.translation import gettext as _

from apps.accounts.models import ParticipantProfile, Role
from apps.consents.models import Consent, ConsentKind
from apps.studies.models import Enrollment, Study
from apps.studies.services import profile_matches

from .models import NotificationPreference


def matching_participants(study: Study):
    """Participants who match the study's criteria AND agreed to be contacted AND didn't opt out."""
    consenting = Consent.objects.active().filter(document__kind=ConsentKind.STUDY_MATCHING_CONTACT).values("user_id")
    opted_out = NotificationPreference.objects.filter(email_matching_studies=False).values("user_id")
    already_enrolled = Enrollment.objects.filter(study=study).values("participant_id")

    profiles = (
        ParticipantProfile.objects.filter(user__role=Role.PARTICIPANT, user__is_active=True, user_id__in=consenting)
        .exclude(user_id__in=opted_out)
        .exclude(user_id__in=already_enrolled)
        .select_related("user")
    )
    # Health fields are encrypted → filter in Python.
    # TODO: batch / iterate in chunks when the participant base grows.
    return [p.user for p in profiles.iterator(chunk_size=500) if profile_matches(study.criteria, p)]


def build_matching_study_email(user, study: Study) -> EmailMessage:
    """
    Deliberately generic: no study title, diagnosis or criteria (an email could reveal health data
    to whoever reads the inbox). Only a link to the study page behind login.
    """
    with translation.override(settings.LANGUAGE_CODE):
        subject = _("A new study may be relevant for you")
        body = _(
            "A new clinical study that may match your profile has been published in the Patient Research "
            "Registry.\n\nLog in to see the details:\n%(link)s\n\n"
            "You can turn these emails off in your settings."
        ) % {"link": f"{settings.FRONTEND_URL}/participant/studies"}
    return EmailMessage(subject=subject, body=body, to=[user.email])


def send_matching_study_emails(study: Study) -> int:
    users = matching_participants(study)
    if not users:
        return 0
    messages = [build_matching_study_email(user, study) for user in users]
    with get_connection() as connection:
        return connection.send_messages(messages) or 0
