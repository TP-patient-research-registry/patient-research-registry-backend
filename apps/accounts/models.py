import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_cryptography.fields import encrypt

from apps.core.fields import EncryptableSmallIntegerField
from apps.core.models import BaseModel

from .managers import UserManager


class Role(models.TextChoices):
    PARTICIPANT = "participant", _("Participant")
    RESEARCHER = "researcher", _("Researcher")
    ORGANIZATION = "organization", _("Organization")
    ADMIN = "admin", _("Administrator")


class Sex(models.TextChoices):
    FEMALE = "female", _("Female")
    MALE = "male", _("Male")
    OTHER = "other", _("Other")


class Region(models.TextChoices):
    """Slovak self-governing regions (kraje)."""

    BA = "BA", "Bratislavský"
    TT = "TT", "Trnavský"
    TN = "TN", "Trenčiansky"
    NR = "NR", "Nitriansky"
    ZA = "ZA", "Žilinský"
    BB = "BB", "Banskobystrický"
    PO = "PO", "Prešovský"
    KE = "KE", "Košický"


class User(AbstractUser):
    """Email is the login; `role` decides which API area the user may access."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARTICIPANT)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        ordering = ("email",)

    def __str__(self):
        return self.email


class Organization(BaseModel):
    """Research institution (hospital, university, pharma company)."""

    name = models.CharField(max_length=255)
    registration_number = models.CharField(_("IČO"), max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        ordering = ("name",)

    def __str__(self):
        return self.name


class ParticipantProfile(BaseModel):
    """
    Health-related data (GDPR art. 9) is encrypted at rest with FIELD_ENCRYPTION_KEY.
    Encrypted fields can't be filtered in SQL — matching happens in Python (see studies.services).
    """

    ENCRYPTED_FIELDS = ("birth_year", "sex", "region", "diagnoses")

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="participant_profile")
    birth_year = encrypt(
        EncryptableSmallIntegerField(
            null=True, blank=True, validators=[MinValueValidator(1900), MaxValueValidator(2100)]
        )
    )
    sex = encrypt(models.CharField(max_length=10, choices=Sex.choices, blank=True))
    region = encrypt(models.CharField(max_length=2, choices=Region.choices, blank=True))
    # ICD-10 codes, e.g. ["E11", "I10"]
    diagnoses = encrypt(models.JSONField(default=list, blank=True))

    def __str__(self):
        return f"Participant profile {self.pk}"


class ResearcherProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="researcher_profile")
    institution = models.CharField(max_length=255, blank=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name="researchers"
    )
    # Set by an administrator after checking the researcher's credentials.
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Researcher profile {self.user}"
