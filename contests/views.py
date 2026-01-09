from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from accounts.permissions import IsSuperUser, IsNotBanned, IsManager
from .models import Contest, ContestRegistration, ContestAnnouncement
from .serializers import (
    ContestListSerializer,
    ContestDetailSerializer,
    ContestCreateSerializer,
    ContestUpdateSerializer,
    ContestRegistrationSerializer,
    ContestAnnouncementSerializer,
    ContestAnnouncementCreateSerializer,
    ManagerListSerializer
)
from .permissions import IsContestManager

User = get_user_model()


# ==================== Contest CRUD (SuperUser) ====================

class ContestListView(generics.ListAPIView):
    """
    List all contests with filters
    GET /api/contests/?status=UPCOMING&manager=john
    """
    serializer_class = ContestListSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_queryset(self):
        queryset = Contest.objects.filter(is_active=True).select_related('manager')
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            from django.utils import timezone
            now = timezone.now()
            
            if status_filter.upper() == 'UPCOMING':
                queryset = queryset.filter(start_time__gt=now)
            elif status_filter.upper() == 'ACTIVE':
                queryset = queryset.filter(start_time__lte=now, end_time__gte=now)
            elif status_filter.upper() == 'ENDED':
                queryset = queryset.filter(end_time__lt=now)
        
        # Filter by manager username
        manager = self.request.query_params.get('manager', None)
        if manager:
            queryset = queryset.filter(manager__username=manager)
        
        return queryset.order_by('-start_time')


class ContestDetailView(generics.RetrieveAPIView):
    """
    Get contest details
    GET /api/contests/<slug>/
    """
    queryset = Contest.objects.filter(is_active=True)
    serializer_class = ContestDetailSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    lookup_field = 'slug'


class ContestCreateView(generics.CreateAPIView):
    """
    Create a new contest (SuperUser only)
    POST /api/contests/create/
    """
    queryset = Contest.objects.all()
    serializer_class = ContestCreateSerializer
    permission_classes = [IsSuperUser]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ContestUpdateView(generics.UpdateAPIView):
    """
    Update a contest (SuperUser only)
    PUT/PATCH /api/contests/<slug>/update/
    """
    queryset = Contest.objects.all()
    serializer_class = ContestUpdateSerializer
    permission_classes = [IsSuperUser]
    lookup_field = 'slug'


class ContestDeleteView(generics.DestroyAPIView):
    """
    Delete a contest (SuperUser only) - soft delete
    DELETE /api/contests/<slug>/delete/
    """
    queryset = Contest.objects.all()
    permission_classes = [IsSuperUser]
    lookup_field = 'slug'
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()


# ==================== Manager Assignment (SuperUser) ====================

class AvailableManagersView(generics.ListAPIView):
    """
    List all managers (for assignment dropdown)
    GET /api/contests/available-managers/
    """
    serializer_class = ManagerListSerializer
    permission_classes = [IsSuperUser]
    
    def get_queryset(self):
        return User.objects.filter(role='MANAGER', is_active=True, is_banned=False)


class AssignManagerView(views.APIView):
    """
    Assign or change manager for a contest (SuperUser only)
    POST /api/contests/<slug>/assign-manager/
    Body: {"manager_id": 5}
    """
    permission_classes = [IsSuperUser]
    
    def post(self, request, slug):
        contest = get_object_or_404(Contest, slug=slug)
        manager_id = request.data.get('manager_id')
        
        if not manager_id:
            return Response(
                {'error': 'manager_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            manager = User.objects.get(id=manager_id)
            if manager.role != 'MANAGER':
                return Response(
                    {'error': 'Selected user is not a Manager'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            contest.manager = manager
            contest.save()
            
            return Response({
                'message': f'Manager {manager.username} assigned successfully',
                'contest': ContestDetailSerializer(contest, context={'request': request}).data
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Manager not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class RemoveManagerView(views.APIView):
    """
    Remove manager from a contest (SuperUser only)
    POST /api/contests/<slug>/remove-manager/
    """
    permission_classes = [IsSuperUser]
    
    def post(self, request, slug):
        contest = get_object_or_404(Contest, slug=slug)
        contest.manager = None
        contest.save()
        
        return Response({
            'message': 'Manager removed successfully',
            'contest': ContestDetailSerializer(contest, context={'request': request}).data
        })


# ==================== Contest Registration ====================

class RegisterForContestView(views.APIView):
    """
    Register for a contest
    POST /api/contests/<slug>/register/
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def post(self, request, slug):
        contest = get_object_or_404(Contest, slug=slug, is_active=True)
        
        # Check if contest is open for registration
        if not contest.can_register:
            return Response(
                {'error': 'Registration is closed for this contest'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check max participants
        if contest.max_participants:
            if contest.total_participants >= contest.max_participants:
                return Response(
                    {'error': 'Contest is full'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if already registered
        if ContestRegistration.objects.filter(user=request.user, contest=contest).exists():
            return Response(
                {'error': 'Already registered for this contest'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Register user
        registration = ContestRegistration.objects.create(
            user=request.user,
            contest=contest
        )
        
        # Update participant count
        contest.total_participants += 1
        contest.save()
        
        return Response({
            'message': 'Successfully registered for contest',
            'registration': ContestRegistrationSerializer(registration).data
        }, status=status.HTTP_201_CREATED)


class UnregisterFromContestView(views.APIView):
    """
    Unregister from a contest
    POST /api/contests/<slug>/unregister/
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def post(self, request, slug):
        contest = get_object_or_404(Contest, slug=slug)
        
        # Check if contest has started
        if contest.is_running or contest.is_ended:
            return Response(
                {'error': 'Cannot unregister from a contest that has started or ended'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            registration = ContestRegistration.objects.get(
                user=request.user,
                contest=contest
            )
            registration.delete()
            
            # Update participant count
            contest.total_participants = max(0, contest.total_participants - 1)
            contest.save()
            
            return Response({
                'message': 'Successfully unregistered from contest'
            })
            
        except ContestRegistration.DoesNotExist:
            return Response(
                {'error': 'Not registered for this contest'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ContestParticipantsView(generics.ListAPIView):
    """
    List all participants of a contest
    GET /api/contests/<slug>/participants/
    """
    serializer_class = ContestRegistrationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        contest = get_object_or_404(Contest, slug=slug)
        return ContestRegistration.objects.filter(contest=contest).select_related('user')


# ==================== Contest Announcements ====================

class ContestAnnouncementsView(generics.ListAPIView):
    """
    List announcements for a contest
    GET /api/contests/<slug>/announcements/
    """
    serializer_class = ContestAnnouncementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        contest = get_object_or_404(Contest, slug=slug)
        return ContestAnnouncement.objects.filter(contest=contest).order_by('-created_at')


class CreateAnnouncementView(generics.CreateAPIView):
    """
    Create an announcement (Manager of the contest only)
    POST /api/contests/<slug>/announcements/create/
    """
    serializer_class = ContestAnnouncementCreateSerializer
    permission_classes = [IsAuthenticated, IsContestManager]
    
    def perform_create(self, serializer):
        slug = self.kwargs.get('slug')
        contest = get_object_or_404(Contest, slug=slug)
        serializer.save(contest=contest, created_by=self.request.user)


# ==================== My Contests ====================

class MyContestsView(generics.ListAPIView):
    """
    Get contests user is registered for
    GET /api/contests/my-contests/
    """
    serializer_class = ContestListSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_queryset(self):
        user = self.request.user
        registered_contest_ids = ContestRegistration.objects.filter(
            user=user
        ).values_list('contest_id', flat=True)
        
        return Contest.objects.filter(
            id__in=registered_contest_ids,
            is_active=True
        ).order_by('-start_time')


class MyManagedContestsView(generics.ListAPIView):
    """
    Get contests managed by current user (Manager only)
    GET /api/contests/my-managed-contests/
    """
    serializer_class = ContestListSerializer
    permission_classes = [IsAuthenticated, IsManager]
    
    def get_queryset(self):
        return Contest.objects.filter(
            manager=self.request.user,
            is_active=True
        ).order_by('-start_time')