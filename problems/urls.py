from django.urls import path
from .views import (
    # Tags
    TagListCreateView,
    TagDetailView,
    
    # Problems
    ProblemListView,
    ProblemDetailView,
    ProblemCreateView,
    ProblemUpdateView,
    ProblemDeleteView,
    
    # Test Cases
    TestCaseListView,
    TestCaseCreateView,
    TestCaseUpdateView,
    TestCaseDeleteView,
    
    # Statistics
    ProblemStatisticsView,
    UserProblemStatsView,
)

app_name = 'problems'

urlpatterns = [
    # Tags
    path('tags/', TagListCreateView.as_view(), name='tag-list-create'),
    path('tags/<int:pk>/', TagDetailView.as_view(), name='tag-detail'),
    
    # Problems
    path('', ProblemListView.as_view(), name='problem-list'),
    path('create/', ProblemCreateView.as_view(), name='problem-create'),
    path('<slug:slug>/', ProblemDetailView.as_view(), name='problem-detail'),
    path('<slug:slug>/update/', ProblemUpdateView.as_view(), name='problem-update'),
    path('<slug:slug>/delete/', ProblemDeleteView.as_view(), name='problem-delete'),
    
    # Test Cases
    path('<slug:slug>/test-cases/', TestCaseListView.as_view(), name='test-case-list'),
    path('<slug:slug>/test-cases/create/', TestCaseCreateView.as_view(), name='test-case-create'),
    path('test-cases/<int:pk>/update/', TestCaseUpdateView.as_view(), name='test-case-update'),
    path('test-cases/<int:pk>/delete/', TestCaseDeleteView.as_view(), name='test-case-delete'),
    
    # Statistics
    path('<slug:slug>/statistics/', ProblemStatisticsView.as_view(), name='problem-statistics'),
    path('my-stats/', UserProblemStatsView.as_view(), name='user-stats'),
]