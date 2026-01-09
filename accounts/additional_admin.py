from django.contrib import admin
from .additional_models import UserActivity, Achievement, UserAchievement


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin for UserActivity model"""
    list_display = ['user', 'date', 'problems_solved', 'submissions_count']
    list_filter = ['date']
    search_fields = ['user__username', 'user__email']
    date_hierarchy = 'date'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """Admin for Achievement model"""
    list_display = ['name', 'achievement_type', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['achievement_type']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """Admin for UserAchievement model"""
    list_display = ['user', 'achievement', 'earned_at']
    list_filter = ['earned_at', 'achievement']
    search_fields = ['user__username', 'achievement__name']
    date_hierarchy = 'earned_at'