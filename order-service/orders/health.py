"""Lightweight liveness and readiness endpoints."""

from django.db import connections
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def liveness(request):
    """Confirm that the Order Service can respond."""
    return JsonResponse({"status": "alive"})


@require_GET
def readiness(request):
    """Confirm that the order database is reachable."""
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "not_ready"}, status=503)

    return JsonResponse({"status": "ready"})
