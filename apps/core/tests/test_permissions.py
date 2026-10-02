"""Guards the "default deny" rule: every API view must declare permissions explicitly."""

import pytest
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.core.permissions import DenyAll

# Views that are intentionally public.
PUBLIC_VIEWS = {"PublicStudyViewSet", "SessionView", "HealthView", "SpectacularAPIView", "SpectacularSwaggerView"}


def iter_api_views(patterns=None, prefix=""):
    for pattern in patterns if patterns is not None else get_resolver().url_patterns:
        if isinstance(pattern, URLResolver):
            yield from iter_api_views(pattern.url_patterns, prefix + str(pattern.pattern))
        elif isinstance(pattern, URLPattern):
            view_class = getattr(pattern.callback, "cls", None)
            if view_class and issubclass(view_class, APIView):
                yield prefix + str(pattern.pattern), view_class


def test_every_api_view_declares_permissions():
    views = list(iter_api_views())
    assert views, "no API views discovered"
    for route, view_class in views:
        permissions = view_class.permission_classes
        assert DenyAll not in permissions, f"{route} relies on the default DenyAll"
        if AllowAny in permissions:
            assert view_class.__name__ in PUBLIC_VIEWS, f"{route} ({view_class.__name__}) is unexpectedly public"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [
        "/api/participant/profile/",
        "/api/participant/consents/",
        "/api/participant/studies/recommended/",
        "/api/participant/my-data/export/",
        "/api/researcher/studies/",
    ],
)
def test_anonymous_is_denied(api_client, url):
    assert api_client.get(url).status_code in (401, 403)


@pytest.mark.django_db
def test_wrong_role_is_denied(participant_client, researcher_client):
    assert participant_client.get("/api/researcher/studies/").status_code == 403
    assert researcher_client.get("/api/participant/profile/").status_code == 403


@pytest.mark.django_db
def test_error_envelope(api_client):
    body = api_client.get("/api/researcher/studies/").json()
    assert body["error"]["status"] == 403
    assert body["error"]["code"] == "not_authenticated"
