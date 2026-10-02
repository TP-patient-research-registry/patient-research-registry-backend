from django.db import transaction

from .models import ParticipantProfile, ResearcherProfile, Role, User


@transaction.atomic
def set_role_and_create_profile(user: User, role: str) -> User:
    """Self-registration may only pick participant or researcher (researchers start unverified)."""
    if role not in (Role.PARTICIPANT, Role.RESEARCHER):
        role = Role.PARTICIPANT
    user.role = role
    user.save(update_fields=["role"])
    ensure_profile(user)
    return user


def ensure_profile(user: User) -> None:
    if user.role == Role.PARTICIPANT:
        ParticipantProfile.objects.get_or_create(user=user)
    elif user.role in (Role.RESEARCHER, Role.ORGANIZATION):
        ResearcherProfile.objects.get_or_create(user=user)


def is_verified_researcher(user: User) -> bool:
    profile = getattr(user, "researcher_profile", None)
    return bool(profile and profile.is_verified)
