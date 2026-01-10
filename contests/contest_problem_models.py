from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import Contest

User = get_user_model()


class ContestProblem(models.Model):
    """
    Problem specific to a contest (created by Manager)
    Separate from general problem pool
    """
    
    class Difficulty(models.TextChoices):
        EASY = 'EASY', _('Easy')
        MEDIUM = 'MEDIUM', _('Medium')
        HARD = 'HARD', _('Hard')
    
    # Contest Association
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='problems',
        verbose_name=_('contest')
    )
    
    # Basic Information
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    
    # Problem Details
    difficulty = models.CharField(
        _('difficulty'),
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM
    )
    points = models.IntegerField(_('points'), default=100)
    
    # Content
    constraints = models.TextField(_('constraints'), blank=True)
    input_format = models.TextField(_('input format'), blank=True)
    output_format = models.TextField(_('output format'), blank=True)
    examples = models.TextField(_('examples'), help_text='Store example inputs/outputs')
    
    # Limits
    time_limit = models.IntegerField(_('time limit (ms)'), default=2000)
    memory_limit = models.IntegerField(_('memory limit (MB)'), default=256)
    
    # Ordering
    order = models.IntegerField(_('order'), default=0, help_text='Display order in contest')
    
    # Statistics
    total_submissions = models.IntegerField(_('total submissions'), default=0)
    accepted_submissions = models.IntegerField(_('accepted submissions'), default=0)
    total_solved = models.IntegerField(_('total users solved'), default=0)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_contest_problems',
        verbose_name=_('created by')
    )
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('contest problem')
        verbose_name_plural = _('contest problems')
        ordering = ['contest', 'order']
        unique_together = ['contest', 'order']
        indexes = [
            models.Index(fields=['contest', 'order']),
            models.Index(fields=['contest', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.contest.title} - {self.title}"
    
    @property
    def acceptance_rate(self):
        """Calculate acceptance rate"""
        if self.total_submissions == 0:
            return 0.0
        return round((self.accepted_submissions / self.total_submissions) * 100, 2)


class ContestTestCase(models.Model):
    """
    Test cases for contest problems
    """
    
    class TestCaseType(models.TextChoices):
        SAMPLE = 'SAMPLE', _('Sample')  # Visible to users
        HIDDEN = 'HIDDEN', _('Hidden')  # Hidden from users
    
    problem = models.ForeignKey(
        ContestProblem,
        on_delete=models.CASCADE,
        related_name='test_cases',
        verbose_name=_('problem')
    )
    
    test_type = models.CharField(
        _('test case type'),
        max_length=10,
        choices=TestCaseType.choices,
        default=TestCaseType.HIDDEN
    )
    
    input_data = models.TextField(_('input data'))
    expected_output = models.TextField(_('expected output'))
    
    # Metadata
    order = models.IntegerField(_('order'), default=0)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('contest test case')
        verbose_name_plural = _('contest test cases')
        ordering = ['problem', 'order']
        indexes = [
            models.Index(fields=['problem', 'order']),
        ]
    
    def __str__(self):
        return f"{self.problem.title} - TestCase {self.order} ({self.test_type})"