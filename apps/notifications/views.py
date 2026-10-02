from rest_framework import generics

from apps.core.permissions import IsParticipant

from .models import NotificationPreference
from .serializers import NotificationPreferenceSerializer


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsParticipant]
    serializer_class = NotificationPreferenceSerializer
    http_method_names = ["get", "patch", "put"]

    def get_object(self):
        preference, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return preference
