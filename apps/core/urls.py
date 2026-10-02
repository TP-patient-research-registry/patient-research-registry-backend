from django.urls import path

from .views import HealthView

public_patterns = [path("health/", HealthView.as_view(), name="health")]
