import factory

from apps.accounts.models import Organization, ParticipantProfile, ResearcherProfile, Role, User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True  # RelatedFactory profiles don't modify the user

    email = factory.Sequence(lambda n: f"user{n}@example.test")
    password = factory.django.Password("test-password-123")
    role = Role.PARTICIPANT


class ParticipantProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ParticipantProfile

    user = factory.SubFactory(UserFactory, role=Role.PARTICIPANT)
    birth_year = 1980
    sex = "female"
    region = "BA"
    diagnoses = factory.LazyFunction(lambda: ["E11.9"])


class ParticipantFactory(UserFactory):
    role = Role.PARTICIPANT
    profile = factory.RelatedFactory(ParticipantProfileFactory, factory_related_name="user")


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Research Institute {n}")
    is_verified = True


class ResearcherProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResearcherProfile

    user = factory.SubFactory(UserFactory, role=Role.RESEARCHER)
    institution = "Demo University"
    organization = factory.SubFactory(OrganizationFactory)
    is_verified = True


class ResearcherFactory(UserFactory):
    role = Role.RESEARCHER
    profile = factory.RelatedFactory(ResearcherProfileFactory, factory_related_name="user")
