from datetime import date

import pytest

from apps.accounts.models import ParticipantProfile
from apps.studies.models import EligibilityCriteria
from apps.studies.services import profile_matches

TODAY = date(2026, 1, 1)


def make(criteria=None, **profile):
    defaults = {"birth_year": 1980, "sex": "female", "region": "BA", "diagnoses": ["E11.9"]}
    return EligibilityCriteria(**(criteria or {})), ParticipantProfile(**{**defaults, **profile})


@pytest.mark.parametrize(
    ("criteria", "profile", "expected"),
    [
        ({}, {}, True),
        ({"min_age": 18, "max_age": 50}, {}, True),
        ({"min_age": 50}, {}, False),
        ({"max_age": 40}, {}, False),
        ({"min_age": 18}, {"birth_year": None}, False),
        ({"sex": "male"}, {}, False),
        ({"regions": ["BA", "TT"]}, {}, True),
        ({"regions": ["KE"]}, {}, False),
        ({"diagnoses": ["E11"]}, {}, True),
        ({"diagnoses": ["I10"]}, {}, False),
    ],
)
def test_profile_matches(criteria, profile, expected):
    c, p = make(criteria, **profile)
    assert profile_matches(c, p, today=TODAY) is expected
