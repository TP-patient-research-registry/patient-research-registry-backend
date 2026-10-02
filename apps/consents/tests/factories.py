import factory
from django.utils import timezone

from apps.accounts.tests.factories import ParticipantFactory
from apps.consents.models import Consent, ConsentDocument, ConsentKind


class ConsentDocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConsentDocument

    kind = ConsentKind.HEALTH_DATA_PROCESSING
    version = factory.Sequence(lambda n: f"1.{n}")
    language = "sk"
    title = "Súhlas so spracúvaním údajov o zdraví"
    text = "Demo consent text."
    published_at = factory.LazyFunction(timezone.now)


class ConsentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Consent

    user = factory.SubFactory(ParticipantFactory)
    document = factory.SubFactory(ConsentDocumentFactory)
