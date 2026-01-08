from django.contrib import admin
from .models import Submission, TestCaseResult


class TestCaseResultInline(admin.TabularInline):
    """Inline admin for test case results"""
    model = TestCaseResult
    extra = 0
    readonly_fields = ['test_case', 'status', 'actual_output', 'execution_time', 'memory_used']
    can_delete = False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Admin for Submission model"""
    list_display = [
        'id', 'user', 'problem', 'language', 'verdict',
        'test_cases_passed', 'total_test_cases',
        'execution_time', 'memory_used', 'submitted_at'
    ]
    list_filter = ['verdict', 'language', 'is_contest_submission', 'submitted_at']
    search_fields = ['user__username', 'user__email', 'problem__title']
    readonly_fields = [
        'user', 'problem', 'verdict', 'execution_time', 'memory_used',
        'test_cases_passed', 'total_test_cases', 'submitted_at'
    ]
    inlines = [TestCaseResultInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'problem', 'language', 'code')
        }),
        ('Execution Results', {
            'fields': ('verdict', 'execution_time', 'memory_used', 
                      'test_cases_passed', 'total_test_cases')
        }),
        ('Error Details', {
            'fields': ('error_message', 'compilation_output'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('is_contest_submission', 'submitted_at')
        }),
    )


@admin.register(TestCaseResult)
class TestCaseResultAdmin(admin.ModelAdmin):
    """Admin for TestCaseResult model"""
    list_display = [
        'submission', 'test_case', 'status',
        'execution_time', 'memory_used', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['submission__id', 'test_case__problem__title']
    readonly_fields = ['submission', 'test_case', 'created_at']