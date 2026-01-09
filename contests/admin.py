from django.contrib import admin
from .models import Contest, ContestRegistration, ContestAnnouncement


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