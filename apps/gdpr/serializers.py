from auditlog.models import LogEntry
from rest_framework import serializers

from .models import DeletionRequest


class DeletionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeletionRequest
        fields = ("id", "status", "reason", "created_at", "processed_at")
        read_only_fields = ("id", "status", "created_at", "processed_at")


class AccessLogEntrySerializer(serializers.ModelSerializer):
    """What happened to the participant's data, and by whom (role only — no staff identities)."""

    action = serializers.SerializerMethodField()
    object_type = serializers.CharField(source="content_type.model", read_only=True)
    actor = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = ("id", "timestamp", "action", "object_type", "actor")
        read_only_fields = fields

    def get_action(self, obj) -> str:
        return {
            LogEntry.Action.CREATE: "create",
            LogEntry.Action.UPDATE: "update",
            LogEntry.Action.DELETE: "delete",
            LogEntry.Action.ACCESS: "access",
        }.get(obj.action, "other")

    def get_actor(self, obj) -> str:
        if obj.actor_id is None:
            return "system"
        if obj.actor_id == self.context["request"].user.pk:
            return "you"
        return obj.actor.role
