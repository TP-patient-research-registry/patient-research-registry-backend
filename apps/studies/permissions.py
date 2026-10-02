from rest_framework.permissions import SAFE_METHODS, BasePermission


class StudyObjectPermission(BasePermission):
    """Object-level permissions on Study via django-guardian."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            perm = "studies.view_study"
        elif request.method == "DELETE":
            perm = "studies.delete_study"
        else:
            perm = "studies.change_study"
        return request.user.has_perm(perm, obj)
