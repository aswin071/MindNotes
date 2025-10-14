"""
Custom permissions for API access control
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Only allow owners of an object to view/edit it"""

    def has_object_permission(self, request, view, obj):
        # Check if object has user_id (MongoDB) or user (PostgreSQL)
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow read-only access to anyone, write access only to owner"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsPremiumUser(permissions.BasePermission):
    """
    Permission to check if user has active premium subscription.
    Used for premium features like 30-day focus programs.
    """
    message = "This feature requires an active Pro subscription."

    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has active subscription
        try:
            from subscriptions.models import Subscription
            subscription = Subscription.objects.get(user=request.user)
            return subscription.is_pro()
        except Subscription.DoesNotExist:
            return False


class IsPremiumUserOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read access to all, but write access only to premium users.
    """
    message = "This action requires an active Pro subscription."

    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for premium users
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            from subscriptions.models import Subscription
            subscription = Subscription.objects.get(user=request.user)
            return subscription.is_pro()
        except Subscription.DoesNotExist:
            return False
