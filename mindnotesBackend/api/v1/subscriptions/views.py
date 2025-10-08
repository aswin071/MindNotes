from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.core.cache import cache

from core.services import ProfileService
from .serializers import (
    ProfileStatsSerializer,
    SubscriptionSerializer,
    PaymentHistorySerializer
)
from subscriptions.models import Subscription, PaymentHistory


class ProfileView(APIView):
    """
    GET /api/v1/profile/

    Returns aggregated profile data for the authenticated user.
    This includes:
    - User information (name, email, avatar)
    - Statistics (total entries, current streak, focus minutes, days using app)
    - Subscription status (Free/Pro plan)
    - User preferences and settings

    Response format matches the Profile screen wireframe requirements.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get profile data with statistics aggregated from PostgreSQL and MongoDB
        """
        user = request.user

        # Try to get from cache first (5 minute cache)
        cache_key = f'profile_stats_{user.id}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            # Get aggregated profile stats from service layer
            profile_data = ProfileService.get_profile_stats(user)

            # Serialize the data
            serializer = ProfileStatsSerializer(profile_data)

            # Cache for 5 minutes
            cache.set(cache_key, serializer.data, 300)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve profile data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscriptionDetailView(APIView):
    """
    GET /api/v1/subscriptions/me/

    Returns detailed subscription information for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's subscription details"""
        try:
            subscription = Subscription.objects.get(user=request.user)
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            # Create default free subscription
            subscription = Subscription.objects.create(
                user=request.user,
                plan='free',
                status='active'
            )
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentHistoryView(APIView):
    """
    GET /api/v1/subscriptions/payments/

    Returns payment history for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's payment history"""
        payments = PaymentHistory.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = PaymentHistorySerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invalidate_profile_cache(request):
    """
    POST /api/v1/profile/invalidate-cache/

    Invalidate profile cache when user updates their profile.
    This should be called after any updates to user data.
    """
    cache_key = f'profile_stats_{request.user.id}'
    cache.delete(cache_key)

    return Response(
        {'message': 'Profile cache invalidated successfully'},
        status=status.HTTP_200_OK
    )
