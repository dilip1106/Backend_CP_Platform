from django.urls import path
from .views import (
    RunCodeView,
    SubmissionCreateView,
    SubmissionListView,
    SubmissionDetailView,
    MySubmissionsView,
    MySubmissionStatsView,
)

app_name = 'submissions'

urlpatterns = [
    # Run code (sample test cases only)
    path('run/', RunCodeView.as_view(), name='run-code'),
    
    # User's submissions (must come before detail view to avoid conflicts)
    path('my-submissions/', MySubmissionsView.as_view(), name='my-submissions'),
    path('my-stats/', MySubmissionStatsView.as_view(), name='my-stats'),
    
    # Submit code (all test cases, saves verdict)
    path('submit/', SubmissionCreateView.as_view(), name='submission-create'),
    
    # List submissions
    path('', SubmissionListView.as_view(), name='submission-list'),
    
    # Submission detail (must be last to avoid conflicts)
    path('<int:pk>/', SubmissionDetailView.as_view(), name='submission-detail'),
]