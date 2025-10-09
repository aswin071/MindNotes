"""
Custom exception handlers for API error responses
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """Custom exception handler for consistent error responses"""

    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Customize the response format
        custom_response_data = {
            'success': False,
            'error': {
                'message': str(exc),
                'details': response.data,
                'code': response.status_code
            }
        }
        response.data = custom_response_data

    return response


class ServiceUnavailableException(Exception):
    """Raised when a service is temporarily unavailable"""
    pass


class CacheException(Exception):
    """Raised when cache operations fail"""
    pass
