from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        return Response(
            {'detail': 'Cannot delete: classroom still has students. Move or delete them first.'},
            status=status.HTTP_409_CONFLICT,
        )
    return exception_handler(exc, context)
