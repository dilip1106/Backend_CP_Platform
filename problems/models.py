from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class Tag(models.Model):
    """
    Tags for categorizing problems (e.g., Arrays, DP, Graphs)
    """
    name = models.CharField(_('tag name'), max_length=50, unique=True)
    slug = models.SlugField(_('slug'), max_length=50, unique=True)
    description = models.TextField(_('description'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Problem(models.Model):
    """
    Coding problem in the general pool (managed by SuperUser)
    """
    
    class Difficulty(models.TextChoices):
        EASY = 'EASY', _('Easy')
        MEDIUM = 'MEDIUM', _('Medium')
        HARD = 'HARD', _('Hard')
    
    # Basic Information
    title = models.CharField(_('title'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    description = models.TextField(_('description'))
    
    # Difficulty and Tags
    difficulty = models.CharField(
        _('difficulty'),
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM
    )
    tags = models.ManyToManyField(Tag, related_name='problems', blank=True)
    
    # Problem Details
    constraints = models.TextField(_('constraints'), blank=True)
    input_format = models.TextField(_('input format'), blank=True)
    output_format = models.TextField(_('output format'), blank=True)
    
    # Examples (stored as JSON or text)
    examples = models.TextField(_('examples'), help_text='Store example inputs/outputs')
    
    # Limits
    time_limit = models.IntegerField(_('time limit (ms)'), default=2000)
    memory_limit = models.IntegerField(_('memory limit (MB)'), default=256)
    
    # Statistics
    total_submissions = models.IntegerField(_('total submissions'), default=0)
    accepted_submissions = models.IntegerField(_('accepted submissions'), default=0)
    total_solved = models.IntegerField(_('total users solved'), default=0)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_problems',
        verbose_name=_('created by')
    )
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('problem')
        verbose_name_plural = _('problems')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['difficulty']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def acceptance_rate(self):
        """Calculate acceptance rate"""
        if self.total_submissions == 0:
            return 0.0
        return round((self.accepted_submissions / self.total_submissions) * 100, 2)
    
    def increment_submissions(self):
        """Increment total submissions"""
        self.total_submissions += 1
        self.save(update_fields=['total_submissions'])
    
    def increment_accepted(self):
        """Increment accepted submissions"""
        self.accepted_submissions += 1
        self.save(update_fields=['accepted_submissions'])
    
    def increment_solved(self):
        """Increment total users who solved"""
        self.total_solved += 1
        self.save(update_fields=['total_solved'])


class TestCase(models.Model):
    """
    Test cases for problems
    """
    
    class TestCaseType(models.TextChoices):
        SAMPLE = 'SAMPLE', _('Sample')  # Visible to users
        HIDDEN = 'HIDDEN', _('Hidden')  # Hidden from users
    
    problem = models.ForeignKey(
        Problem,
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
        verbose_name = _('test case')
        verbose_name_plural = _('test cases')
        ordering = ['problem', 'order']
        indexes = [
            models.Index(fields=['problem', 'order']),
        ]
    
    def __str__(self):
        return f"{self.problem.title} - TestCase {self.order} ({self.test_type})"


class ProblemSolveStatus(models.Model):
    """
    Track which problems each user has solved/attempted
    """
    
    class Status(models.TextChoices):
        ATTEMPTED = 'ATTEMPTED', _('Attempted')
        SOLVED = 'SOLVED', _('Solved')
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='problem_statuses',
        verbose_name=_('user')
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='user_statuses',
        verbose_name=_('problem')
    )
    status = models.CharField(
        _('status'),
        max_length=10,
        choices=Status.choices,
        default=Status.ATTEMPTED
    )
    
    first_solved_at = models.DateTimeField(_('first solved at'), null=True, blank=True)
    last_attempted_at = models.DateTimeField(_('last attempted at'), auto_now=True)
    
    class Meta:
        verbose_name = _('problem solve status')
        verbose_name_plural = _('problem solve statuses')
        unique_together = ['user', 'problem']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['problem', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.problem.title} ({self.status})"