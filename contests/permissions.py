from rest_framework import permissions
from .models import Contest


class IsContestManager(permissions.BasePermission):
    """
    Permission class to check if user is the manager of the contest
    """
    message = "You must be the manager of this contest to perform this action."
    
    def has_permission(self, request, view):
        # Get contest slug from URL
        slug = view.kwargs.get('slug')
        if not slug:
            return False
        
        try:
            contest = Contest.objects.get(slug=slug)
            return (
                request.user and
                request.user.is_authenticated and
                contest.manager == request.user
            )
        except Contest.DoesNotExist:
            return False


class IsContestManagerOrReadOnly(permissions.BasePermission):
    """
    Permission: Contest manager can edit, others can only read
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        slug = view.kwargs.get('slug')
        if not slug:
            return False
        
        try:
            contest = Contest.objects.get(slug=slug)
            return (
                request.user and
                request.user.is_authenticated and
                contest.manager == request.user
            )
        except Contest.DoesNotExist:
            return False