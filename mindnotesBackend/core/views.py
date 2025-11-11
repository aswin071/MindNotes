"""
Core views for health checks and system monitoring
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
import mongoengine
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring system status
    Returns 200 if all systems operational, 503 if any critical service is down
    """
    health_status = {
        'status': 'healthy',
        'services': {}
    }

    all_healthy = True

    # Check PostgreSQL
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health_status['services']['postgresql'] = {
            'status': 'healthy',
            'message': 'Connected'
        }
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {str(e)}")
        health_status['services']['postgresql'] = {
            'status': 'unhealthy',
            'message': str(e)
        }
        all_healthy = False

    # Check MongoDB
    try:
        # Ping MongoDB
        mongoengine.connection.get_db().command('ping')
        health_status['services']['mongodb'] = {
            'status': 'healthy',
            'message': 'Connected'
        }
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")
        health_status['services']['mongodb'] = {
            'status': 'unhealthy',
            'message': str(e)
        }
        all_healthy = False

    # Check Redis/Cache
    try:
        cache.set('health_check', 'ok', 10)
        cache_value = cache.get('health_check')
        if cache_value == 'ok':
            health_status['services']['cache'] = {
                'status': 'healthy',
                'message': 'Connected'
            }
        else:
            raise Exception("Cache read/write mismatch")
    except Exception as e:
        logger.warning(f"Cache health check failed: {str(e)}")
        health_status['services']['cache'] = {
            'status': 'degraded',
            'message': str(e)
        }
        # Cache failure is not critical, just degraded performance

    # Overall status
    if not all_healthy:
        health_status['status'] = 'unhealthy'
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response(health_status, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check for load balancers
    Simpler check - just returns 200 if server is running
    """
    return Response({'status': 'ready'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness check for Kubernetes/container orchestration
    Just confirms the application is alive and responding
    """
    return Response({'status': 'alive'}, status=status.HTTP_200_OK)
