import logging
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, OperationalError
import traceback

logger = logging.getLogger(__name__)

class ExceptionHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Log the exception with full context
        error_details = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'request_method': request.method,
            'request_path': request.path,
            'user_id': request.user.id if request.user.is_authenticated else 'anonymous',
            'traceback': traceback.format_exc()
        }
        
        logger.error(
            f"Exception in request {request.method} {request.path}: {type(exception).__name__}: {str(exception)}",
            exc_info=True,
            extra=error_details
        )

        # Handle specific exception types
        if isinstance(exception, PermissionDenied):
            return JsonResponse({'error': 'Permission denied', 'details': str(exception)}, status=403)
        
        if isinstance(exception, OperationalError):
            return JsonResponse({
                'error': 'Database connection error',
                'details': str(exception),
                'suggestion': 'Check database configuration and connection'
            }, status=500)
        
        if isinstance(exception, DatabaseError):
            return JsonResponse({
                'error': 'Database error occurred',
                'details': str(exception),
                'type': type(exception).__name__
            }, status=500)

        # For other exceptions, let Django handle them
        return None