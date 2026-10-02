import logging

from celery import shared_task

from apps.studies.models import Study, StudyStatus

from .services import send_matching_study_emails

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=5)
def notify_matching_participants(self, study_id: str) -> int:
    """Triggered when a study is published (studies.services.publish_study)."""
    study = Study.objects.select_related("criteria").filter(pk=study_id, status=StudyStatus.PUBLISHED).first()
    if study is None:
        return 0
    sent = send_matching_study_emails(study)
    logger.info("Study %s published: notified %d participants", study_id, sent)
    return sent
