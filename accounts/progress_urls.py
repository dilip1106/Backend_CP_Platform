from django.urls import path
from .progress_views import (
    UserProgressView,
    UserActivityCalendarView,
    SolvedProblemsView,
    AttemptedProblemsView,
    GlobalLeaderboardView,
    UserPublicProfileView,
    MyProfileStatsView,
    AchievementsListView,
    UserAchievementsView,
    CompareUsersView,
)

urlpatterns = [
    # User Progress
    path('progress/', UserProgressView.as_view(), name='user-progress'),
    path('activity-calendar/', UserActivityCalendarView.as_view(), name='activity-calendar'),
    path('my-profile-stats/', MyProfileStatsView.as_view(), name='my-profile-stats'),
    
    # Solved/Attempted Problems
    path('solved-problems/', SolvedProblemsView.as_view(), name='solved-problems'),
    path('attempted-problems/', AttemptedProblemsView.as_view(), name='attempted-problems'),
    
    # Leaderboard
    path('leaderboard/', GlobalLeaderboardView.as_view(), name='leaderboard'),
    
    # Public Profiles
    path('<str:username>/profile/', UserPublicProfileView.as_view(), name='user-public-profile'),
    
    # Achievements
    path('my-achievements/', UserAchievementsView.as_view(), name='my-achievements'),
    
    # Compare Users
    path('compare/', CompareUsersView.as_view(), name='compare-users'),
]