from rest_framework import serializers

from .models import Questionnaire, Response


class QuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = ("id", "study", "title", "schema", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "study", "created_at", "updated_at")


class ParticipantResponseSerializer(serializers.ModelSerializer):
    submit = serializers.BooleanField(write_only=True, default=False)

    class Meta:
        model = Response
        fields = ("id", "questionnaire", "data", "submitted_at", "submit", "updated_at")
        read_only_fields = ("id", "questionnaire", "submitted_at", "updated_at")


class PseudonymizedResponseSerializer(serializers.ModelSerializer):
    """Researcher view: answers keyed by the per-study pseudonym, never the participant's identity."""

    participant_id = serializers.SerializerMethodField()

    class Meta:
        model = Response
        fields = ("id", "participant_id", "data", "submitted_at")
        read_only_fields = fields

    def get_participant_id(self, obj) -> str | None:
        pseudonyms: dict = self.context.get("pseudonyms", {})
        pseudonym = pseudonyms.get(obj.participant_id)
        return str(pseudonym) if pseudonym else None
