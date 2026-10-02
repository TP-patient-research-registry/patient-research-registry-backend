from django.urls import path, re_path

from .views import ParticipantProfileView, ResearcherProfileView, SessionView

# Matches both /api/auth/session and /api/auth/session/ (the frontend calls it without a slash).
auth_patterns = [re_path(r"^session/?$", SessionView.as_view(), name="auth-session")]

participant_patterns = [path("profile/", ParticipantProfileView.as_view(), name="participant-profile")]

researcher_patterns = [path("profile/", ResearcherProfileView.as_view(), name="researcher-profile")]
