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
    # User's submissions (must come before detail view to avoid conflicts)
    path('my-submissions/', MySubmissionsView.as_view(), name='my-submissions'),
    path('my-stats/', MySubmissionStatsView.as_view(), name='my-stats'),
    
    # Submit code
    path('submit/', SubmissionCreateView.as_view(), name='submission-create'),
    
    # List submissions
    path('', SubmissionListView.as_view(), name='submission-list'),
    
    # Submission detail (must be last to avoid conflicts)
    path('<int:pk>/', SubmissionDetailView.as_view(), name='submission-detail'),
]