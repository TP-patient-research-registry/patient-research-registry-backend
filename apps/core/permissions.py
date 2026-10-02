from rest_framework.permissions import BasePermission


class DenyAll(BasePermission):
    """Default permission (see REST_FRAMEWORK settings): views must opt in explicitly."""

    def has_permission(self, request, view):
        return False


class HasRole(BasePermission):
    """Authenticated user with one of `roles`. Use the concrete subclasses below."""

    roles: tuple[str, ...] = ()

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.role in self.roles)


class IsParticipant(HasRole):
    roles = ("participant",)


class IsResearcher(HasRole):
    """Researchers and organization accounts share the researcher API."""

    roles = ("researcher", "organization")


class IsAdminRole(HasRole):
    roles = ("admin",)
