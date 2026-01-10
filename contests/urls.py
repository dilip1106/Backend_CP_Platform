from django.urls import path
from .views import (
    # Contest CRUD
    ContestListView,
    ContestDetailView,
    ContestCreateView,
    ContestUpdateView,
    ContestDeleteView,
    
    # Manager Assignment
    AvailableManagersView,
    AssignManagerView,
    RemoveManagerView,
    
    # Contest Registration
    RegisterForContestView,
    UnregisterFromContestView,
    ContestParticipantsView,
    
    # Announcements
    ContestAnnouncementsView,
    CreateAnnouncementView,
    
    # My Contests
    MyContestsView,
    MyManagedContestsView,
)

from .contest_problem_views import (
    # Contest Problems
    ContestProblemsListView,
    ContestProblemDetailView,
    ContestProblemCreateView,
    ContestProblemUpdateView,
    ContestProblemDeleteView,
    ReorderProblemsView,
    
    # Test Cases
    ContestProblemTestCasesView,
    ContestTestCaseCreateView,
    ContestTestCaseUpdateView,
    ContestTestCaseDeleteView,
    
    # Statistics
    ContestProblemStatsView,
)

from .contest_participation_views import (
    # Contest Participation
    SubmitContestSolutionView,
    ContestLeaderboardView,
    DetailedLeaderboardView,
    MyContestDashboardView,
    MyContestSubmissionsView,
    ContestSubmissionDetailView,
)

app_name = 'contests'

urlpatterns = [
    # Contest CRUD (SuperUser)
    path('', ContestListView.as_view(), name='contest-list'),
    path('create/', ContestCreateView.as_view(), name='contest-create'),
    path('<slug:slug>/', ContestDetailView.as_view(), name='contest-detail'),
    path('<slug:slug>/update/', ContestUpdateView.as_view(), name='contest-update'),
    path('<slug:slug>/delete/', ContestDeleteView.as_view(), name='contest-delete'),
    
    # Manager Assignment (SuperUser)
    path('available-managers/', AvailableManagersView.as_view(), name='available-managers'),
    path('<slug:slug>/assign-manager/', AssignManagerView.as_view(), name='assign-manager'),
    path('<slug:slug>/remove-manager/', RemoveManagerView.as_view(), name='remove-manager'),
    
    # Contest Registration
    path('<slug:slug>/register/', RegisterForContestView.as_view(), name='register'),
    path('<slug:slug>/unregister/', UnregisterFromContestView.as_view(), name='unregister'),
    path('<slug:slug>/participants/', ContestParticipantsView.as_view(), name='participants'),
    
    # Announcements
    path('<slug:slug>/announcements/', ContestAnnouncementsView.as_view(), name='announcements'),
    path('<slug:slug>/announcements/create/', CreateAnnouncementView.as_view(), name='create-announcement'),
    
    # My Contests
    path('my-contests/', MyContestsView.as_view(), name='my-contests'),
    path('my-managed-contests/', MyManagedContestsView.as_view(), name='my-managed-contests'),
    
    # Contest Problems (Phase 6)
    path('<slug:slug>/problems/', ContestProblemsListView.as_view(), name='contest-problems'),
    path('<slug:slug>/problems/create/', ContestProblemCreateView.as_view(), name='create-problem'),
    path('<slug:slug>/problems/reorder/', ReorderProblemsView.as_view(), name='reorder-problems'),
    path('<slug:slug>/problems/stats/', ContestProblemStatsView.as_view(), name='problem-stats'),
    path('<slug:slug>/problems/<int:pk>/', ContestProblemDetailView.as_view(), name='problem-detail'),
    path('<slug:slug>/problems/<int:pk>/update/', ContestProblemUpdateView.as_view(), name='update-problem'),
    path('<slug:slug>/problems/<int:pk>/delete/', ContestProblemDeleteView.as_view(), name='delete-problem'),
    
    # Test Cases (Phase 6)
    path('<slug:slug>/problems/<int:pk>/test-cases/', ContestProblemTestCasesView.as_view(), name='test-cases'),
    path('<slug:slug>/problems/<int:pk>/test-cases/create/', ContestTestCaseCreateView.as_view(), name='create-test-case'),
    path('test-cases/<int:pk>/update/', ContestTestCaseUpdateView.as_view(), name='update-test-case'),
    path('test-cases/<int:pk>/delete/', ContestTestCaseDeleteView.as_view(), name='delete-test-case'),
    
    # Contest Participation (Phase 7 & 8)
    path('<slug:slug>/submit/', SubmitContestSolutionView.as_view(), name='submit-solution'),
    path('<slug:slug>/my-dashboard/', MyContestDashboardView.as_view(), name='my-dashboard'),
    path('<slug:slug>/my-submissions/', MyContestSubmissionsView.as_view(), name='my-contest-submissions'),
    path('<slug:slug>/leaderboard/', ContestLeaderboardView.as_view(), name='leaderboard'),
    path('<slug:slug>/leaderboard/detailed/', DetailedLeaderboardView.as_view(), name='detailed-leaderboard'),
    path('submissions/<int:pk>/', ContestSubmissionDetailView.as_view(), name='contest-submission-detail'),
]