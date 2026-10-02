"""Fill the database with FAKE demo data. Never contains real people or real health data."""

import random

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

DEMO_PASSWORD = "demo-password-123"  # noqa: S105 — demo accounts only


class Command(BaseCommand):
    help = "Create fake demo data (organizations, researchers, participants, studies, questionnaires)."

    def add_arguments(self, parser):
        parser.add_argument("--participants", type=int, default=30)
        parser.add_argument("--force", action="store_true", help="Allow running with DEBUG=False.")

    def handle(self, *args, participants: int, force: bool, **options):
        if not settings.DEBUG and not force:
            raise CommandError("Refusing to seed demo data with DEBUG=False (use --force on non-production only).")
        try:
            from faker import Faker
        except ImportError as exc:  # dev dependency
            raise CommandError("seed_demo needs dev dependencies: `uv sync --group dev`.") from exc

        with transaction.atomic():
            self._seed(Faker("sk_SK"), participants)

    def _seed(self, fake, participant_count: int):
        from allauth.account.models import EmailAddress

        from apps.accounts.models import Organization, ParticipantProfile, Region, ResearcherProfile, Role, Sex, User
        from apps.consents.models import ConsentDocument, ConsentKind
        from apps.consents.services import grant_consent
        from apps.questionnaires.models import Questionnaire
        from apps.studies.models import EligibilityCriteria, Enrollment, EnrollmentStatus, StudyStatus
        from apps.studies.services import create_study

        if User.objects.filter(email__endswith="@demo.example").exists():
            self.stdout.write(self.style.WARNING("Demo data already present, skipping."))
            return

        now = timezone.now()
        documents = {
            kind: ConsentDocument.objects.create(
                kind=kind,
                version="1.0",
                language="sk",
                title=label,
                text=fake.paragraph(nb_sentences=8),
                published_at=now,
            )
            for kind, label in ConsentKind.choices
        }

        org = Organization.objects.create(
            name="Demo Univerzitná nemocnica", registration_number="00000000", is_verified=True
        )
        researcher = User.objects.create_user(
            "researcher@demo.example", DEMO_PASSWORD, role=Role.RESEARCHER, first_name="Demo", last_name="Researcher"
        )
        ResearcherProfile.objects.create(user=researcher, institution=org.name, organization=org, is_verified=True)
        org_user = User.objects.create_user("organization@demo.example", DEMO_PASSWORD, role=Role.ORGANIZATION)
        ResearcherProfile.objects.create(user=org_user, institution=org.name, organization=org, is_verified=True)

        diagnoses = ["E11", "I10", "J45", "M54", "F32", "G43", "K21"]
        participants = []
        for i in range(participant_count):
            user = User.objects.create_user(
                f"participant{i + 1}@demo.example",
                DEMO_PASSWORD,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            ParticipantProfile.objects.create(
                user=user,
                birth_year=random.randint(1940, 2005),
                sex=random.choice([Sex.FEMALE, Sex.MALE]),
                region=random.choice(Region.values),
                diagnoses=random.sample(diagnoses, k=random.randint(0, 2)),
            )
            for document in documents.values():
                grant_consent(user, document)
            participants.append(user)

        study_specs = [
            ("Demo: Nová liečba diabetu 2. typu", {"min_age": 40, "max_age": 75, "diagnoses": ["E11"]}),
            ("Demo: Kontrola krvného tlaku", {"min_age": 30, "diagnoses": ["I10"]}),
            ("Demo: Astma u mladých dospelých", {"min_age": 18, "max_age": 35, "diagnoses": ["J45"]}),
            ("Demo: Zdraví dobrovoľníci - Bratislava", {"min_age": 18, "max_age": 60, "regions": ["BA"]}),
        ]
        for title, criteria in study_specs:
            study = create_study(researcher, title=title, description=fake.paragraph(nb_sentences=6), organization=org)
            EligibilityCriteria.objects.filter(study=study).update(**criteria)
            # Set directly instead of publish_study() so seeding doesn't email anyone.
            study.status, study.published_at = StudyStatus.PUBLISHED, now
            study.save()
            Questionnaire.objects.create(
                study=study,
                title="Vstupný dotazník",
                schema={
                    "pages": [
                        {
                            "elements": [
                                {"type": "rating", "name": "wellbeing", "title": "Ako sa dnes cítite?"},
                                {"type": "comment", "name": "notes", "title": "Poznámky"},
                            ]
                        }
                    ]
                },
            )
            for user in random.sample(participants, k=min(5, len(participants))):
                Enrollment.objects.get_or_create(
                    participant=user,
                    study=study,
                    defaults={"status": random.choice([EnrollmentStatus.APPLIED, EnrollmentStatus.ENROLLED])},
                )

        # Email verification is mandatory: mark all demo addresses as verified.
        EmailAddress.objects.bulk_create(
            EmailAddress(user=u, email=u.email, verified=True, primary=True)
            for u in User.objects.filter(email__endswith="@demo.example")
        )

        create_study(researcher, title="Demo: Koncept štúdie", description=fake.paragraph(), organization=org)

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data created. Log in as researcher@demo.example / participant1@demo.example "
                f"(password: {DEMO_PASSWORD})."
            )
        )
