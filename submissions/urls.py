from django.urls import path
from .views import (
    SubmissionCreateView,
    SubmissionListView,
    SubmissionDetailView,
    MySubmissionsView,
    MySubmissionStatsView,
)

app_name = 'submissions'

urlpatterns = [
    # Submit code
    path('submit/', SubmissionCreateView.as_view(), name='submission-create'),
    
    # List submissions
    path('', SubmissionListView.as_view(), name='submission-list'),
    path('<int:pk>/', SubmissionDetailView.as_view(), name='submission-detail'),
    
    # User's submissions
    path('my-submissions/', MySubmissionsView.as_view(), name='my-submissions'),
    path('my-stats/', MySubmissionStatsView.as_view(), name='my-stats'),
]