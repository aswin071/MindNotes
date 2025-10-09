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
