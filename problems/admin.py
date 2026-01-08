from django.contrib import admin
from .models import Problem, TestCase, Tag, ProblemSolveStatus


class TestCaseInline(admin.TabularInline):
    """Inline admin for test cases"""
    model = TestCase
    extra = 1
    fields = ['test_type', 'input_data', 'expected_output', 'order', 'is_active']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin for Tag model"""
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    """Admin for Problem model"""
    list_display = [
        'title', 'difficulty', 'total_submissions', 
        'acceptance_rate', 'total_solved', 'is_active', 'created_at'
    ]
    list_filter = ['difficulty', 'is_active', 'created_at', 'tags']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    readonly_fields = [
        'total_submissions', 'accepted_submissions', 
        'total_solved', 'acceptance_rate', 'created_at', 'updated_at'
    ]
    inlines = [TestCaseInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'difficulty', 'tags')
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


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    """Admin for TestCase model"""
    list_display = ['problem', 'test_type', 'order', 'is_active', 'created_at']
    list_filter = ['test_type', 'is_active', 'created_at']
    search_fields = ['problem__title']


@admin.register(ProblemSolveStatus)
class ProblemSolveStatusAdmin(admin.ModelAdmin):
    """Admin for ProblemSolveStatus model"""
    list_display = ['user', 'problem', 'status', 'first_solved_at', 'last_attempted_at']
    list_filter = ['status', 'first_solved_at']
    search_fields = ['user__username', 'user__email', 'problem__title']