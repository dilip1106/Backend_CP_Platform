from django.contrib import admin
from .models import Contest, ContestRegistration, ContestAnnouncement
from .contest_problem_models import ContestProblem, ContestTestCase
from .contest_submission_models import ContestSubmission, ContestParticipant, ProblemSolveStatus


class ContestTestCaseInline(admin.TabularInline):
    """Inline admin for contest test cases"""
    model = ContestTestCase
    extra = 1
    fields = ['test_type', 'input_data', 'expected_output', 'order', 'is_active']


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    """Admin for Contest model"""
    list_display = [
        'title', 'manager', 'start_time', 'end_time',
        'total_participants', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'is_public', 'start_time', 'scoring_type']
    search_fields = ['title', 'description', 'manager__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['total_participants', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'duration')
        }),
        ('Management', {
            'fields': ('created_by', 'manager')
        }),
        ('Settings', {
            'fields': ('is_public', 'is_active', 'max_participants', 'scoring_type')
        }),
        ('Rules', {
            'fields': ('rules',)
        }),
        ('Statistics', {
            'fields': ('total_participants',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ContestRegistration)
class ContestRegistrationAdmin(admin.ModelAdmin):
    """Admin for ContestRegistration model"""
    list_display = ['user', 'contest', 'registered_at']
    list_filter = ['registered_at', 'contest']
    search_fields = ['user__username', 'contest__title']
    date_hierarchy = 'registered_at'


@admin.register(ContestAnnouncement)
class ContestAnnouncementAdmin(admin.ModelAdmin):
    """Admin for ContestAnnouncement model"""
    list_display = ['title', 'contest', 'created_by', 'created_at']
    list_filter = ['created_at', 'contest']
    search_fields = ['title', 'content', 'contest__title']
    date_hierarchy = 'created_at'


@admin.register(ContestProblem)
class ContestProblemAdmin(admin.ModelAdmin):
    """Admin for ContestProblem model"""
    list_display = [
        'title', 'contest', 'difficulty', 'points', 'order',
        'total_submissions', 'acceptance_rate', 'is_active'
    ]
    list_filter = ['difficulty', 'is_active', 'contest']
    search_fields = ['title', 'description', 'contest__title']
    readonly_fields = ['total_submissions', 'accepted_submissions', 'total_solved', 'acceptance_rate']
    inlines = [ContestTestCaseInline]
    
    fieldsets = (
        ('Contest', {
            'fields': ('contest', 'order')
        }),
        ('Basic Information', {
            'fields': ('title', 'description', 'difficulty', 'points')
        }),
        ('Problem Details', {
            'fields': ('constraints', 'input_format', 'output_format', 'examples')
        }),
        ('Limits', {
            'fields': ('time_limit', 'memory_limit')
        }),
        ('Statistics', {
            'fields': ('total_submissions', 'accepted_submissions', 'acceptance_rate', 'total_solved')
        }),
        ('Metadata', {
            'fields': ('created_by', 'is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(ContestTestCase)
class ContestTestCaseAdmin(admin.ModelAdmin):
    """Admin for ContestTestCase model"""
    list_display = ['problem', 'test_type', 'order', 'is_active', 'created_at']
    list_filter = ['test_type', 'is_active', 'created_at']
    search_fields = ['problem__title']


@admin.register(ContestSubmission)
class ContestSubmissionAdmin(admin.ModelAdmin):
    """Admin for ContestSubmission model"""
    list_display = ['user', 'contest', 'problem', 'verdict', 'language', 'submitted_at']
    list_filter = ['verdict', 'language', 'contest', 'submitted_at']
    search_fields = ['user__username', 'problem__title', 'contest__title']
    readonly_fields = ['submitted_at']


@admin.register(ContestParticipant)
class ContestParticipantAdmin(admin.ModelAdmin):
    """Admin for ContestParticipant model"""
    list_display = ['user', 'contest', 'rank', 'total_score', 'problems_solved', 'total_time']
    list_filter = ['contest']
    search_fields = ['user__username', 'contest__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProblemSolveStatus)
class ProblemSolveStatusAdmin(admin.ModelAdmin):
    """Admin for ProblemSolveStatus model"""
    list_display = ['participant', 'problem', 'status', 'score', 'attempts', 'solve_time']
    list_filter = ['status']
    search_fields = ['participant__user__username', 'problem__title']