import logging
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError

logger = logging.getLogger(__name__)

class ExceptionHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Log the exception with full context
        logger.error(
            f"Exception in request {request.method} {request.path}: {str(exception)}",
            exc_info=True,
            extra={
                'request_method': request.method,
                'request_path': request.path,
                'user_id': request.user.id if request.user.is_authenticated else 'anonymous',
            }
        )

        # Handle specific exception types
        if isinstance(exception, PermissionDenied):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        if isinstance(exception, DatabaseError):
            return JsonResponse({'error': 'Database error occurred'}, status=500)

        # For other exceptions, let Django handle them
        return None