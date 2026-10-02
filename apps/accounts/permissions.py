from rest_framework.permissions import BasePermission

from .services import is_verified_researcher


class IsVerifiedResearcher(BasePermission):
    message = "Your researcher account has not been verified yet."

    def has_permission(self, request, view):
        return is_verified_researcher(request.user)
