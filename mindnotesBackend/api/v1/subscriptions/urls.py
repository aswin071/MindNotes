from django.urls import path
from .views import (
    ProfileView,
    SubscriptionDetailView,
    PaymentHistoryView,
    invalidate_profile_cache
)


urlpatterns = [
    # Profile endpoint - Main API for Profile screen
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/invalidate-cache/', invalidate_profile_cache, name='profile-invalidate-cache'),

    # Subscription endpoints
    path('me', SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('payments', PaymentHistoryView.as_view(), name='payment-history'),
]

