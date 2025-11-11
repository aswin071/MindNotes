from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from authentication.models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    PasswordChangeSerializer,
    GoogleAuthSerializer,
    SignupWithGoogleSerializer,
)
from helpers.common import success_response, error_response


def _get_tokens_for_user(user: User):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = _get_tokens_for_user(user)
            data = {
                'user': UserSerializer(user).data,
                'tokens': tokens,
            }
            return success_response(data=data, success_message='Registration successful', status=status.HTTP_201_CREATED)
        return error_response(errors=serializer.errors, error_message='Invalid data', status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, error_message='Invalid credentials', status=status.HTTP_400_BAD_REQUEST)
        user = serializer.validated_data['user']
        tokens = _get_tokens_for_user(user)
        data = {
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }
        return success_response(data=data, success_message='Login successful', status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(data={'user': UserSerializer(request.user).data}, success_message='Profile fetched')

    def patch(self, request):
        from .serializers import UserUpdateSerializer
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(data={'user': serializer.data}, success_message='Profile updated')
        return error_response(errors=serializer.errors, error_message='Validation failed', status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return success_response(success_message='Password changed successfully')
        return error_response(errors=serializer.errors, error_message='Validation failed', status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return error_response(error_message='Refresh token required', status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as exc:
            return error_response(error_message='Invalid refresh token', exception_info=str(exc), status=status.HTTP_400_BAD_REQUEST)
        return success_response(success_message='Logged out successfully')


# Re-export TokenRefreshView but wrap response
class RefreshTokenWrappedView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return success_response(data={'tokens': response.data}, success_message='Token refreshed')
        return error_response(errors=response.data, error_message='Could not refresh token', status=response.status_code)


class GoogleSignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, error_message='Invalid Google token', status=status.HTTP_400_BAD_REQUEST)

        google_info = serializer.validated_data['google']
        email = google_info['email']

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': google_info.get('full_name') or '',
                'is_verified': True,
            }
        )
        if created:
            # Create profile for new user
            from authentication.models import UserProfile
            UserProfile.objects.create(user=user)

        tokens = _get_tokens_for_user(user)
        data = {
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'provider': 'google',
        }
        return success_response(data=data, success_message='Google sign-in successful', status=status.HTTP_200_OK)


class GoogleSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupWithGoogleSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, error_message='Invalid Google token', status=status.HTTP_400_BAD_REQUEST)
        google_info = serializer.validated_data['google']
        onboarding_answers = serializer.validated_data.get('onboarding_answers', {})
        dob = serializer.validated_data.get('dob')
        gender = serializer.validated_data.get('gender', '')
        profession = serializer.validated_data.get('profession', '')

        email = google_info['email']
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': google_info.get('full_name') or '',
                'is_verified': True,
                'dob': dob,
                'gender': gender,
                'profession': profession,
            }
        )
        if created:
            from authentication.models import UserProfile
            profile = UserProfile.objects.create(user=user)
            if onboarding_answers:
                profile.onboarding_answers = onboarding_answers
                profile.save(update_fields=['onboarding_answers'])

        tokens = _get_tokens_for_user(user)
        data = {
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'provider': 'google',
        }
        return success_response(data=data, success_message='Google signup successful', status=status.HTTP_200_OK)


# ============ DASHBOARD API ============

class HomeView(APIView):
    """
    GET /api/v1/authentication/dashboard/

    Returns complete dashboard data for the Home screen.
    This is the main endpoint for the Dashboard/Home page wireframe.

    Aggregates data from:
    - User profile (greeting, avatar, streak)
    - Daily prompts (prompt of the day)
    - Focus programs (active program progress)
    - Mood categories (mood tracker options)
    - Today's activity stats

    All data is user-specific and cached for 2 minutes for performance.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Get complete dashboard data"""
        from django.core.cache import cache
        from core.services import DashboardService
        from .serializers import DashboardSerializer

        user = request.user

        # Cache key for dashboard
        cache_key = f'dashboard_{user.id}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return success_response(cached_data, status=status.HTTP_200_OK)

        try:
            # Get aggregated dashboard data from service layer
            dashboard_data = DashboardService.get_dashboard_data(user)

            # Serialize the data
            serializer = DashboardSerializer(dashboard_data)

            # Cache for 2 minutes
            cache.set(cache_key, serializer.data, 120)

            return success_response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return error_response(
                {'error': f'Failed to retrieve dashboard data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

