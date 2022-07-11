from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsAdminOrIsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(request.user == obj.creator or request.user.is_staff)

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS and view.action != 'favorites':
            return True

        return bool(request.user and request.user.is_authenticated or request.user.is_staff)