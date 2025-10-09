"""
Custom middleware for performance and monitoring
"""
import time
import logging
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestTimingMiddleware(MiddlewareMixin):
    """Track request processing time"""

    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            response['X-Request-Duration'] = str(duration)

            # Log slow requests (> 1 second)
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s"
                )

        return response


class CacheHeaderMiddleware(MiddlewareMixin):
    """Add cache control headers for static content"""

    def process_response(self, request, response):
        # Cache static files for 1 year
        if request.path.startswith('/static/'):
            response['Cache-Control'] = 'public, max-age=31536000'
        # Don't cache API responses by default
        elif request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response
