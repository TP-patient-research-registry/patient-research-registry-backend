from rest_framework import serializers

from .models import Consent, ConsentDocument


class ConsentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentDocument
        fields = ("id", "kind", "version", "language", "title", "text", "published_at")
        read_only_fields = fields


class ConsentSerializer(serializers.ModelSerializer):
    document = ConsentDocumentSerializer(read_only=True)
    document_id = serializers.PrimaryKeyRelatedField(
        source="document",
        queryset=ConsentDocument.objects.filter(published_at__isnull=False),
        write_only=True,
    )
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Consent
        fields = ("id", "document", "document_id", "granted_at", "withdrawn_at", "is_active")
        read_only_fields = ("id", "granted_at", "withdrawn_at", "is_active")
