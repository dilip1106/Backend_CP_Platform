from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class UserActivity(models.Model):
    """
    Track daily user activity for heat map calendar
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('user')
    )
    date = models.DateField(_('date'))
    problems_solved = models.IntegerField(_('problems solved'), default=0)
    submissions_count = models.IntegerField(_('submissions count'), default=0)
    
    class Meta:
        verbose_name = _('user activity')
        verbose_name_plural = _('user activities')
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', '-date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"


class Achievement(models.Model):
    """
    Achievement/Badge system
    """
    
    class AchievementType(models.TextChoices):
        FIRST_SOLVE = 'FIRST_SOLVE', _('First Problem Solved')
        SOLVE_10 = 'SOLVE_10', _('Solved 10 Problems')
        SOLVE_50 = 'SOLVE_50', _('Solved 50 Problems')
        SOLVE_100 = 'SOLVE_100', _('Solved 100 Problems')
        SOLVE_STREAK_7 = 'SOLVE_STREAK_7', _('7 Day Streak')
        SOLVE_STREAK_30 = 'SOLVE_STREAK_30', _('30 Day Streak')
        ALL_EASY = 'ALL_EASY', _('All Easy Problems')
        FIRST_CONTEST = 'FIRST_CONTEST', _('First Contest')
    
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'))
    achievement_type = models.CharField(
        _('achievement type'),
        max_length=20,
        choices=AchievementType.choices,
        unique=True
    )
    icon = models.CharField(_('icon'), max_length=50, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('achievement')
        verbose_name_plural = _('achievements')
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """
    Track achievements earned by users
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='earned_achievements',
        verbose_name=_('user')
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='earned_by',
        verbose_name=_('achievement')
    )
    earned_at = models.DateTimeField(_('earned at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('user achievement')
        verbose_name_plural = _('user achievements')
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"