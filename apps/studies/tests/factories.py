import factory
from django.utils import timezone

from apps.accounts.tests.factories import ParticipantFactory, ResearcherFactory
from apps.studies.models import EligibilityCriteria, Enrollment, Study, StudyStatus
from apps.studies.services import create_study


class StudyFactory(factory.django.DjangoModelFactory):
    """Created through the service so the owner gets guardian object permissions."""

    class Meta:
        model = Study

    title = factory.Sequence(lambda n: f"Study {n}")
    description = "Demo study description."
    owner = factory.SubFactory(ResearcherFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return create_study(**kwargs)


class PublishedStudyFactory(StudyFactory):
    status = StudyStatus.PUBLISHED
    published_at = factory.LazyFunction(timezone.now)


class EnrollmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Enrollment

    participant = factory.SubFactory(ParticipantFactory)
    study = factory.SubFactory(PublishedStudyFactory)


def set_criteria(study: Study, **criteria) -> EligibilityCriteria:
    EligibilityCriteria.objects.filter(study=study).update(**criteria)
    study.criteria.refresh_from_db()
    return study.criteria
