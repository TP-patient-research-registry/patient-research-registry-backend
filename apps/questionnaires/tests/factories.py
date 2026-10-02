import factory

from apps.questionnaires.models import Questionnaire
from apps.studies.tests.factories import PublishedStudyFactory


class QuestionnaireFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Questionnaire

    study = factory.SubFactory(PublishedStudyFactory)
    title = "Baseline questionnaire"
    schema = factory.LazyFunction(lambda: {"pages": [{"elements": [{"type": "text", "name": "q1"}]}]})
