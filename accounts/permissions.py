from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """
    Permission class to check if user has SuperUser role
    """
    message = "You must be a SuperUser to perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'SUPER_USER'
        )


class IsManager(permissions.BasePermission):
    """
    Permission class to check if user has Manager role
    """
    message = "You must be a Manager to perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'MANAGER'
        )


class IsNormalUser(permissions.BasePermission):
    """
    Permission class to check if user has Normal User role
    """
    message = "You must be a Normal User to perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'NORMAL_USER'
        )


class IsSuperUserOrManager(permissions.BasePermission):
    """
    Permission class to check if user is SuperUser or Manager
    """
    message = "You must be a SuperUser or Manager to perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['SUPER_USER', 'MANAGER']
        )


class IsOwnerOrSuperUser(permissions.BasePermission):
    """
    Permission class to check if user is the owner of the object or SuperUser
    """
    message = "You can only access your own data."
    
    def has_object_permission(self, request, view, obj):
        # SuperUser has full access
        if request.user.role == 'SUPER_USER':
            return True
        
        # Check if obj is the user themselves
        if hasattr(obj, 'id'):
            return obj.id == request.user.id
        
        return False


class IsNotBanned(permissions.BasePermission):
    """
    Permission class to check if user is not banned
    """
    message = "Your account has been banned. Please contact support."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            not request.user.is_banned
        )


class ReadOnly(permissions.BasePermission):
    """
    Permission class for read-only access
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsSuperUserOrReadOnly(permissions.BasePermission):
    """
    Permission class: SuperUser can do anything, others can only read
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'SUPER_USER'
        )