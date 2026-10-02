import pytest


@pytest.mark.django_db
def test_health(api_client):
    response = api_client.get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_openapi_schema_is_served(api_client):
    response = api_client.get("/api/schema/")
    assert response.status_code == 200
    assert b"/participant/profile/" in response.content
