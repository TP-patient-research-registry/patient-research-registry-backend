from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    """
    Uniform error envelope:
        {"error": {"status": 400, "code": "invalid", "detail": "...", "fields": {...} | null}}
    """
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))
    elif isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # unhandled → 500 via Django (details never leak with DEBUG=False)

    if isinstance(exc, exceptions.ValidationError):
        detail, fields = "Invalid input.", response.data if isinstance(response.data, dict) else None
        if fields and set(fields) == {"non_field_errors"}:
            detail, fields = " ".join(map(str, fields["non_field_errors"])), None
        code = "invalid"
    else:
        detail = response.data.get("detail", "") if isinstance(response.data, dict) else str(response.data)
        fields = None
        code = getattr(exc, "default_code", "error")
        if hasattr(exc, "get_codes"):
            codes = exc.get_codes()
            code = codes if isinstance(codes, str) else code

    response.data = {"error": {"status": response.status_code, "code": code, "detail": str(detail), "fields": fields}}
    return response


def error_response(detail: str, code: str = "error", http_status: int = status.HTTP_400_BAD_REQUEST):
    return Response(
        {"error": {"status": http_status, "code": code, "detail": detail, "fields": None}}, status=http_status
    )
