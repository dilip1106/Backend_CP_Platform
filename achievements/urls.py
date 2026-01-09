from django.urls import path
from accounts.progress_views import AchievementsListView

app_name = 'achievements'

urlpatterns = [
    path('', AchievementsListView.as_view(), name='achievement-list'),
]