from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin
    """
    list_display = ['email', 'username', 'role', 'total_solved', 'is_active', 'is_banned', 'date_joined']
    list_filter = ['role', 'is_active', 'is_banned', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'bio', 'avatar', 'country')}),
        (_('Role & Permissions'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_banned')}),
        (_('Statistics'), {'fields': ('total_solved', 'easy_solved', 'medium_solved', 'hard_solved')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'total_solved', 
                      'easy_solved', 'medium_solved', 'hard_solved']
    
    def get_readonly_fields(self, request, obj=None):
        """
        Make role field read-only for non-superusers
        """
        readonly = list(self.readonly_fields)
        if not request.user.is_superuser and obj:
            readonly.append('role')
        return readonly