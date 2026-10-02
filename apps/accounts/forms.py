from django import forms

from .models import Role
from .services import set_role_and_create_profile

SIGNUP_ROLES = [(Role.PARTICIPANT, Role.PARTICIPANT.label), (Role.RESEARCHER, Role.RESEARCHER.label)]


class SignupForm(forms.Form):
    """Extra signup fields for allauth (ACCOUNT_SIGNUP_FORM_CLASS); also used by the headless API."""

    role = forms.ChoiceField(choices=SIGNUP_ROLES, required=False)

    def signup(self, request, user):
        set_role_and_create_profile(user, self.cleaned_data.get("role") or Role.PARTICIPANT)
