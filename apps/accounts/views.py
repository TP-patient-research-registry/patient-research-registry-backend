from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsParticipant, IsResearcher

from .models import ParticipantProfile, ResearcherProfile
from .serializers import ParticipantProfileSerializer, ResearcherProfileSerializer, SessionSerializer


@method_decorator(ensure_csrf_cookie, name="get")
class SessionView(APIView):
    """
    Current user + role. Used by the frontend route guard (Next.js proxy) and to bootstrap
    the `csrftoken` cookie. Always 200: `user` is null for anonymous visitors.
    """

    permission_classes = [AllowAny]

    @extend_schema(responses=SessionSerializer)
    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        return Response(SessionSerializer({"is_authenticated": user is not None, "user": user}).data)


class ParticipantProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsParticipant]
    serializer_class = ParticipantProfileSerializer
    http_method_names = ["get", "patch", "put"]

    def get_object(self):
        profile, _ = ParticipantProfile.objects.get_or_create(user=self.request.user)
        return profile


class ResearcherProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsResearcher]
    serializer_class = ResearcherProfileSerializer
    http_method_names = ["get", "patch", "put"]

    def get_object(self):
        profile, _ = ResearcherProfile.objects.get_or_create(user=self.request.user)
        return profile
