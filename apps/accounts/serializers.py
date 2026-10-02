from rest_framework import serializers

from .models import Organization, ParticipantProfile, Region, ResearcherProfile, Sex, User


class SessionUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "role", "first_name", "last_name")


class SessionSerializer(serializers.Serializer):
    is_authenticated = serializers.BooleanField()
    user = SessionUserSerializer(allow_null=True)


class ParticipantProfileSerializer(serializers.ModelSerializer):
    sex = serializers.ChoiceField(choices=Sex.choices, allow_blank=True, required=False)
    region = serializers.ChoiceField(choices=Region.choices, allow_blank=True, required=False)
    diagnoses = serializers.ListField(
        child=serializers.RegexField(r"^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$"), required=False
    )

    class Meta:
        model = ParticipantProfile
        fields = ("birth_year", "sex", "region", "diagnoses", "updated_at")
        read_only_fields = ("updated_at",)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "is_verified")
        read_only_fields = fields


class ResearcherProfileSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = ResearcherProfile
        fields = ("institution", "organization", "is_verified")
        read_only_fields = ("organization", "is_verified")
