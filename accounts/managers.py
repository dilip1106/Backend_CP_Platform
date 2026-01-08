from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    for authentication instead of username.
    """
    
    def create_user(self, email, username, password=None, **extra_fields):
        """
        Create and save a regular user with the given email, username and password.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not username:
            raise ValueError(_('The Username field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email, username and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'SUPER_USER')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, username, password, **extra_fields)
    
    def create_manager(self, email, username, password=None, **extra_fields):
        """
        Create and save a Manager user.
        """
        extra_fields.setdefault('role', 'MANAGER')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        return self.create_user(email, username, password, **extra_fields)
    
    def create_normal_user(self, email, username, password=None, **extra_fields):
        """
        Create and save a Normal user.
        """
        extra_fields.setdefault('role', 'NORMAL_USER')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        return self.create_user(email, username, password, **extra_fields)
    
    def get_superusers(self):
        """Get all superusers"""
        return self.filter(role='SUPER_USER')
    
    def get_managers(self):
        """Get all managers"""
        return self.filter(role='MANAGER')
    
    def get_normal_users(self):
        """Get all normal users"""
        return self.filter(role='NORMAL_USER')
    
    def get_active_users(self):
        """Get all active users"""
        return self.filter(is_active=True, is_banned=False)