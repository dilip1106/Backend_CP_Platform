from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import Contest
from .contest_problem_models import ContestProblem

User = get_user_model()


class ContestSubmission(models.Model):
    """
    Code submission during a contest
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
    
    # Contest Information
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='contest_submissions',
        verbose_name=_('contest')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contest_submissions',
        verbose_name=_('user')
    )
    problem = models.ForeignKey(
        ContestProblem,
        on_delete=models.CASCADE,
        related_name='contest_submissions',
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
    
    # Timestamps
    submitted_at = models.DateTimeField(_('submitted at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('contest submission')
        verbose_name_plural = _('contest submissions')
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['contest', 'user', '-submitted_at']),
            models.Index(fields=['contest', 'problem']),
            models.Index(fields=['user', 'verdict']),
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


class ContestParticipant(models.Model):
    """
    Track participant performance in a contest
    """
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_('contest')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contest_participations',
        verbose_name=_('user')
    )
    
    # Score Calculation
    total_score = models.IntegerField(_('total score'), default=0)
    problems_solved = models.IntegerField(_('problems solved'), default=0)
    
    # Time Calculation (for tiebreaker)
    total_time = models.IntegerField(_('total time (minutes)'), default=0)  # Time from contest start to last AC
    penalty_time = models.IntegerField(_('penalty time (minutes)'), default=0)  # Penalty for wrong submissions
    
    # Ranking
    rank = models.IntegerField(_('rank'), null=True, blank=True)
    
    # Metadata
    last_submission_time = models.DateTimeField(_('last submission time'), null=True, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('contest participant')
        verbose_name_plural = _('contest participants')
        unique_together = ['contest', 'user']
        ordering = ['contest', '-total_score', 'total_time']
        indexes = [
            models.Index(fields=['contest', '-total_score', 'total_time']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.contest.title} (Rank: {self.rank})"


class ProblemSolveStatus(models.Model):
    """
    Track which problems each participant has solved in a contest
    """
    
    class Status(models.TextChoices):
        ATTEMPTED = 'ATTEMPTED', _('Attempted')
        SOLVED = 'SOLVED', _('Solved')
    
    participant = models.ForeignKey(
        ContestParticipant,
        on_delete=models.CASCADE,
        related_name='problem_statuses',
        verbose_name=_('participant')
    )
    problem = models.ForeignKey(
        ContestProblem,
        on_delete=models.CASCADE,
        verbose_name=_('problem')
    )
    
    status = models.CharField(
        _('status'),
        max_length=10,
        choices=Status.choices,
        default=Status.ATTEMPTED
    )
    
    # Scoring
    score = models.IntegerField(_('score'), default=0)  # Points earned for this problem
    attempts = models.IntegerField(_('attempts'), default=0)  # Number of submissions
    wrong_attempts = models.IntegerField(_('wrong attempts'), default=0)  # Failed submissions before AC
    
    # Time Tracking
    solve_time = models.IntegerField(_('solve time (minutes)'), null=True, blank=True)  # Time from start to AC
    first_solved_at = models.DateTimeField(_('first solved at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('problem solve status')
        verbose_name_plural = _('problem solve statuses')
        unique_together = ['participant', 'problem']
        indexes = [
            models.Index(fields=['participant', 'status']),
        ]
    
    def __str__(self):
        return f"{self.participant.user.username} - {self.problem.title} ({self.status})"