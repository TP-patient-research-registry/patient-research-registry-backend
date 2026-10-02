from rest_framework import serializers

from .models import EligibilityCriteria, Enrollment, EnrollmentStatus, Study


class EligibilityCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EligibilityCriteria
        fields = ("min_age", "max_age", "sex", "regions", "diagnoses")

    def validate(self, attrs):
        min_age, max_age = attrs.get("min_age"), attrs.get("max_age")
        if min_age is not None and max_age is not None and min_age > max_age:
            raise serializers.ValidationError({"max_age": "Must be greater than or equal to min_age."})
        return attrs


class PublicStudySerializer(serializers.ModelSerializer):
    organization = serializers.CharField(source="organization.name", default=None, read_only=True)
    criteria = EligibilityCriteriaSerializer(read_only=True)

    class Meta:
        model = Study
        fields = ("id", "title", "description", "status", "organization", "published_at", "results_summary", "criteria")
        read_only_fields = fields


class ResearcherStudySerializer(serializers.ModelSerializer):
    criteria = EligibilityCriteriaSerializer(read_only=True)
    enrollment_count = serializers.IntegerField(source="enrollments.count", read_only=True)

    class Meta:
        model = Study
        fields = (
            "id",
            "title",
            "description",
            "status",
            "organization",
            "results_summary",
            "published_at",
            "criteria",
            "enrollment_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status", "published_at", "organization", "created_at", "updated_at")


class EnrollmentSerializer(serializers.ModelSerializer):
    """Participant's own view of an enrollment."""

    study = PublicStudySerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ("id", "study", "status", "created_at", "updated_at")
        read_only_fields = fields


class PseudonymizedEnrollmentSerializer(serializers.ModelSerializer):
    """Researcher's view: only the per-study pseudonym, never name or email."""

    participant_id = serializers.UUIDField(source="pseudonym", read_only=True)
    status = serializers.ChoiceField(choices=EnrollmentStatus.choices)

    class Meta:
        model = Enrollment
        fields = ("participant_id", "status", "created_at", "updated_at")
        read_only_fields = ("participant_id", "created_at", "updated_at")
