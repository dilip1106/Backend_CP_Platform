from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with role-based access control.
    Roles: SUPER_USER, MANAGER, NORMAL_USER
    """
    
    class Role(models.TextChoices):
        SUPER_USER = 'SUPER_USER', _('Super User')
        MANAGER = 'MANAGER', _('Manager')
        NORMAL_USER = 'NORMAL_USER', _('Normal User')
    
    # Basic Information
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), max_length=150, unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    
    # Role
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Role.choices,
        default=Role.NORMAL_USER
    )
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_banned = models.BooleanField(_('banned'), default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    last_login = models.DateTimeField(_('last login'), auto_now=True)
    
    # Profile
    bio = models.TextField(_('bio'), blank=True, max_length=500)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True, null=True)
    country = models.CharField(_('country'), max_length=100, blank=True)
    
    # Statistics (will be updated by signals)
    total_solved = models.IntegerField(_('total problems solved'), default=0)
    easy_solved = models.IntegerField(_('easy problems solved'), default=0)
    medium_solved = models.IntegerField(_('medium problems solved'), default=0)
    hard_solved = models.IntegerField(_('hard problems solved'), default=0)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip() or self.username
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.username
    
    @property
    def is_superuser_role(self):
        """Check if user has SuperUser role"""
        return self.role == self.Role.SUPER_USER
    
    @property
    def is_manager_role(self):
        """Check if user has Manager role"""
        return self.role == self.Role.MANAGER
    
    @property
    def is_normal_user_role(self):
        """Check if user has Normal User role"""
        return self.role == self.Role.NORMAL_USER
    
    def promote_to_manager(self):
        """Promote user to Manager role"""
        if self.role == self.Role.NORMAL_USER:
            self.role = self.Role.MANAGER
            self.save(update_fields=['role'])
            return True
        return False
    
    def demote_to_normal_user(self):
        """Demote user to Normal User role"""
        if self.role == self.Role.MANAGER:
            self.role = self.Role.NORMAL_USER
            self.save(update_fields=['role'])
            return True
        return False
    
    def ban_user(self):
        """Ban the user"""
        self.is_banned = True
        self.is_active = False
        self.save(update_fields=['is_banned', 'is_active'])
    
    def unban_user(self):
        """Unban the user"""
        self.is_banned = False
        self.is_active = True
        self.save(update_fields=['is_banned', 'is_active'])