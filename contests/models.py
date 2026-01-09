from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Contest(models.Model):
    """
    Contest created by SuperUser and managed by assigned Manager
    """
    
    class Status(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', _('Not Started')
        ACTIVE = 'ACTIVE', _('Active')
        ENDED = 'ENDED', _('Ended')
    
    # Basic Information
    title = models.CharField(_('title'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    description = models.TextField(_('description'))
    
    # Timing
    start_time = models.DateTimeField(_('start time'))
    end_time = models.DateTimeField(_('end time'))
    duration = models.IntegerField(_('duration (minutes)'), help_text='Contest duration in minutes')
    
    # Management
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_contests',
        verbose_name=_('created by')
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_contests',
        limit_choices_to={'role': 'MANAGER'},
        verbose_name=_('assigned manager')
    )
    
    # Settings
    is_public = models.BooleanField(_('public'), default=True)
    is_active = models.BooleanField(_('active'), default=True)
    max_participants = models.IntegerField(_('max participants'), null=True, blank=True)
    
    # Rules
    rules = models.TextField(_('contest rules'), blank=True)
    scoring_type = models.CharField(
        _('scoring type'),
        max_length=20,
        choices=[
            ('STANDARD', 'Standard'),
            ('ICPC', 'ICPC'),
        ],
        default='STANDARD'
    )
    
    # Statistics
    total_participants = models.IntegerField(_('total participants'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('contest')
        verbose_name_plural = _('contests')
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['start_time']),
            models.Index(fields=['manager']),
            models.Index(fields=['-start_time']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def status(self):
        """Get current contest status"""
        now = timezone.now()
        if now < self.start_time:
            return self.Status.NOT_STARTED
        elif now > self.end_time:
            return self.Status.ENDED
        else:
            return self.Status.ACTIVE
    
    @property
    def is_upcoming(self):
        """Check if contest is upcoming"""
        return self.status == self.Status.NOT_STARTED
    
    @property
    def is_running(self):
        """Check if contest is currently running"""
        return self.status == self.Status.ACTIVE
    
    @property
    def is_ended(self):
        """Check if contest has ended"""
        return self.status == self.Status.ENDED
    
    @property
    def can_register(self):
        """Check if users can still register"""
        return self.is_upcoming and self.is_active
    
    @property
    def time_until_start(self):
        """Get time until contest starts"""
        if self.is_upcoming:
            return self.start_time - timezone.now()
        return None
    
    @property
    def time_remaining(self):
        """Get time remaining in contest"""
        if self.is_running:
            return self.end_time - timezone.now()
        return None


class ContestRegistration(models.Model):
    """
    Track which users are registered for contests
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contest_registrations',
        verbose_name=_('user')
    )
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name=_('contest')
    )
    
    registered_at = models.DateTimeField(_('registered at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('contest registration')
        verbose_name_plural = _('contest registrations')
        unique_together = ['user', 'contest']
        ordering = ['-registered_at']
        indexes = [
            models.Index(fields=['user', 'contest']),
            models.Index(fields=['contest']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.contest.title}"


class ContestAnnouncement(models.Model):
    """
    Announcements for contests (by Manager)
    """
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='announcements',
        verbose_name=_('contest')
    )
    title = models.CharField(_('title'), max_length=200)
    content = models.TextField(_('content'))
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('created by')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('contest announcement')
        verbose_name_plural = _('contest announcements')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contest.title} - {self.title}"