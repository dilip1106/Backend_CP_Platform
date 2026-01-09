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
]