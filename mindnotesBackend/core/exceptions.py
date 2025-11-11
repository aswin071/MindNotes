"""
Custom exception handlers for API error responses
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Custom exception handler for consistent error responses"""

    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Log the exception
    request = context.get('request')
    logger.error(
        f"API Exception: {type(exc).__name__} - {str(exc)} | "
        f"Path: {request.path if request else 'N/A'} | "
        f"Method: {request.method if request else 'N/A'}",
        exc_info=True
    )

    if response is not None:
        # Customize the response format
        custom_response_data = {
            'success': False,
            'error': {
                'message': str(exc),
                'details': response.data,
                'code': response.status_code,
                'type': type(exc).__name__
            }
        }
        response.data = custom_response_data
    else:
        # Handle unexpected exceptions
        custom_response_data = {
            'success': False,
            'error': {
                'message': 'An unexpected error occurred',
                'details': str(exc),
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'type': type(exc).__name__
            }
        }
        response = Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response


class ServiceUnavailableException(Exception):
    """Raised when a service is temporarily unavailable"""
    def __init__(self, service_name="Service", message=None):
        self.service_name = service_name
        self.message = message or f"{service_name} is temporarily unavailable"
        super().__init__(self.message)


class CacheException(Exception):
    """Raised when cache operations fail"""
    def __init__(self, operation="operation", message=None):
        self.operation = operation
        self.message = message or f"Cache {operation} failed"
        super().__init__(self.message)


class DatabaseConnectionException(Exception):
    """Raised when database connection fails"""
    def __init__(self, database="database", message=None):
        self.database = database
        self.message = message or f"Failed to connect to {database}"
        super().__init__(self.message)


class PromptGenerationException(Exception):
    """Raised when prompt generation fails"""
    def __init__(self, reason="Unknown", message=None):
        self.reason = reason
        self.message = message or f"Prompt generation failed: {reason}"
        super().__init__(self.message)


class ValidationException(Exception):
    """Raised for data validation errors"""
    def __init__(self, field=None, message="Validation error"):
        self.field = field
        self.message = f"{message} (field: {field})" if field else message
        super().__init__(self.message)


class RateLimitException(Exception):
    """Raised when rate limit is exceeded"""
    def __init__(self, limit=None, message=None):
        self.limit = limit
        self.message = message or f"Rate limit exceeded: {limit}"
        super().__init__(self.message)
