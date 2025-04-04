from rest_framework import permissions
from django.utils import timezone

class CanDeleteFootballField(permissions.BasePermission):
    message = "Cannot delete field with future bookings"

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admins can always delete
        if request.user.role == 'admin':
            return True
            
        # Owners can only delete their own fields without future bookings
        if request.user == obj.owner:
            future_bookings = obj.field_bookings.filter(
                end_time__gt=timezone.now()
            ).exists()
            return not future_bookings
            
        return False
    
class IsFieldOwner(permissions.BasePermission):
    """Allows access to field owners and admins"""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.field.owner == request.user

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Write access only for owners/admins"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role in ['admin', 'owner']

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user or request.user.role == 'admin'