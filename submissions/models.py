from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from problems.models import Problem

User = get_user_model()


class Submission(models.Model):
    """
    Code submission for a problem
    """
    
    class Language(models.TextChoices):
        PYTHON = 'PYTHON', _('Python 3')
        JAVA = 'JAVA', _('Java')
        CPP = 'CPP', _('C++')
        JAVASCRIPT = 'JAVASCRIPT', _('JavaScript')
        C = 'C', _('C')
    
    class Verdict(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        RUNNING = 'RUNNING', _('Running')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        WRONG_ANSWER = 'WRONG_ANSWER', _('Wrong Answer')
        TIME_LIMIT_EXCEEDED = 'TIME_LIMIT_EXCEEDED', _('Time Limit Exceeded')
        MEMORY_LIMIT_EXCEEDED = 'MEMORY_LIMIT_EXCEEDED', _('Memory Limit Exceeded')
        RUNTIME_ERROR = 'RUNTIME_ERROR', _('Runtime Error')
        COMPILATION_ERROR = 'COMPILATION_ERROR', _('Compilation Error')
        INTERNAL_ERROR = 'INTERNAL_ERROR', _('Internal Error')
    
    # Basic Information
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('user')
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('problem')
    )
    
    # Code Details
    code = models.TextField(_('source code'))
    language = models.CharField(
        _('language'),
        max_length=20,
        choices=Language.choices
    )
    
    # Execution Results
    verdict = models.CharField(
        _('verdict'),
        max_length=30,
        choices=Verdict.choices,
        default=Verdict.PENDING
    )
    
    # Statistics
    execution_time = models.IntegerField(_('execution time (ms)'), null=True, blank=True)
    memory_used = models.IntegerField(_('memory used (KB)'), null=True, blank=True)
    
    # Test Case Results
    test_cases_passed = models.IntegerField(_('test cases passed'), default=0)
    total_test_cases = models.IntegerField(_('total test cases'), default=0)
    
    # Error Details
    error_message = models.TextField(_('error message'), blank=True)
    compilation_output = models.TextField(_('compilation output'), blank=True)
    
    # Judge0 Integration
    judge0_token = models.CharField(_('Judge0 token'), max_length=100, blank=True)
    
    # Metadata
    is_contest_submission = models.BooleanField(_('contest submission'), default=False)
    submitted_at = models.DateTimeField(_('submitted at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('submission')
        verbose_name_plural = _('submissions')
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['user', '-submitted_at']),
            models.Index(fields=['problem', '-submitted_at']),
            models.Index(fields=['verdict']),
            models.Index(fields=['-submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.problem.title} ({self.verdict})"
    
    @property
    def is_accepted(self):
        """Check if submission is accepted"""
        return self.verdict == self.Verdict.ACCEPTED
    
    @property
    def pass_percentage(self):
        """Calculate percentage of test cases passed"""
        if self.total_test_cases == 0:
            return 0.0
        return round((self.test_cases_passed / self.total_test_cases) * 100, 2)


class TestCaseResult(models.Model):
    """
    Individual test case execution result
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        WRONG_ANSWER = 'WRONG_ANSWER', _('Wrong Answer')
        TIME_LIMIT_EXCEEDED = 'TIME_LIMIT_EXCEEDED', _('Time Limit Exceeded')
        MEMORY_LIMIT_EXCEEDED = 'MEMORY_LIMIT_EXCEEDED', _('Memory Limit Exceeded')
        RUNTIME_ERROR = 'RUNTIME_ERROR', _('Runtime Error')
    
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='test_case_results',
        verbose_name=_('submission')
    )
    test_case = models.ForeignKey(
        'problems.TestCase',
        on_delete=models.CASCADE,
        verbose_name=_('test case')
    )
    
    status = models.CharField(
        _('status'),
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Execution Details
    actual_output = models.TextField(_('actual output'), blank=True)
    execution_time = models.IntegerField(_('execution time (ms)'), null=True, blank=True)
    memory_used = models.IntegerField(_('memory used (KB)'), null=True, blank=True)
    error_message = models.TextField(_('error message'), blank=True)
    
    # Judge0 Integration
    judge0_token = models.CharField(_('Judge0 token'), max_length=100, blank=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('test case result')
        verbose_name_plural = _('test case results')
        ordering = ['test_case__order']
        indexes = [
            models.Index(fields=['submission']),
        ]
    
    def __str__(self):
        return f"{self.submission.id} - TestCase {self.test_case.order} ({self.status})"