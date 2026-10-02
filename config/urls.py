from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.accounts import urls as accounts_urls
from apps.consents import urls as consents_urls
from apps.core import urls as core_urls
from apps.gdpr import urls as gdpr_urls
from apps.notifications import urls as notifications_urls
from apps.questionnaires import urls as questionnaires_urls
from apps.studies import urls as studies_urls

participant_patterns = [
    *accounts_urls.participant_patterns,
    *consents_urls.participant_patterns,
    *studies_urls.participant_patterns,
    *questionnaires_urls.participant_patterns,
    *notifications_urls.participant_patterns,
    *gdpr_urls.participant_patterns,
]

researcher_patterns = [
    *accounts_urls.researcher_patterns,
    *studies_urls.researcher_patterns,
    *questionnaires_urls.researcher_patterns,
]

api_patterns = [
    # Our session endpoint first, then django-allauth headless (/api/auth/browser/v1/...).
    path("auth/", include(accounts_urls.auth_patterns)),
    path("auth/", include("allauth.headless.urls")),
    path("participant/", include(participant_patterns)),
    path("researcher/", include(researcher_patterns)),
    *studies_urls.public_patterns,
    *core_urls.public_patterns,
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
]
