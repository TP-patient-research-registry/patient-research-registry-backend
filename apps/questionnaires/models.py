from django.conf import settings
from django.db import models
from django_cryptography.fields import encrypt

from apps.core.models import BaseModel
from apps.studies.models import Study


class Questionnaire(BaseModel):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="questionnaires")
    title = models.CharField(max_length=255)
    # SurveyJS JSON definition (https://surveyjs.io/form-library/documentation/design-survey/create-a-simple-survey)
    schema = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Response(BaseModel):
    """A participant's answers. Answers are health data → encrypted at rest."""

    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name="responses")
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questionnaire_responses"
    )
    # SurveyJS result object.
    data = encrypt(models.JSONField(default=dict))
    # Null while the participant is still filling it in (draft).
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=("questionnaire", "participant"), name="unique_questionnaire_response")
        ]

    def __str__(self):
        return f"Response to {self.questionnaire}"
