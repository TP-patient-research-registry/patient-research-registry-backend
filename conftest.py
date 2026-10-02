import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import ParticipantFactory, ResearcherFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def participant(db):
    return ParticipantFactory()


@pytest.fixture
def researcher(db):
    return ResearcherFactory()


@pytest.fixture
def participant_client(participant):
    client = APIClient()
    client.force_login(participant)
    return client


@pytest.fixture
def researcher_client(researcher):
    client = APIClient()
    client.force_login(researcher)
    return client
