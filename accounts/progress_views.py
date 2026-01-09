from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Window, F
from django.db.models.functions import RowNumber
from datetime import timedelta
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .permissions import IsNotBanned
from .progress_serializers import (
    UserProgressSerializer,
    UserActivitySerializer,
    LeaderboardSerializer,
    UserProfileStatsSerializer,
    SolvedProblemSerializer,
    AchievementSerializer,
    UserAchievementSerializer,
)
from .additional_models import UserActivity, Achievement, UserAchievement
from problems.models import Problem, ProblemSolveStatus
from submissions.models import Submission

User = get_user_model()


class UserProgressView(generics.GenericAPIView):
    """
    Get comprehensive user progress statistics
    GET /api/users/progress/
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    serializer_class = UserProgressSerializer
    
    @extend_schema(
        responses=UserProgressSerializer,
        description='Get comprehensive user progress statistics',
        summary='Get User Progress'
    )
    def get(self, request):
        user = request.user
        
        # Submission stats
        submissions = Submission.objects.filter(user=user)
        total_submissions = submissions.count()
        accepted = submissions.filter(verdict='ACCEPTED').count()
        acceptance_rate = round((accepted / total_submissions * 100), 2) if total_submissions > 0 else 0.0
        
        # Problem stats
        total_attempted = ProblemSolveStatus.objects.filter(user=user).count()
        total_problems = Problem.objects.filter(is_active=True).count()
        
        # Calculate rank
        users_with_rank = User.objects.annotate(
            rank=Window(
                expression=RowNumber(),
                order_by=F('total_solved').desc()
            )
        )
        user_rank = users_with_rank.get(id=user.id).rank
        total_users = User.objects.count()
        
        data = {
            'total_solved': user.total_solved,
            'easy_solved': user.easy_solved,
            'medium_solved': user.medium_solved,
            'hard_solved': user.hard_solved,
            'total_submissions': total_submissions,
            'acceptance_rate': acceptance_rate,
            'total_attempted': total_attempted,
            'total_problems': total_problems,
            'global_rank': user_rank,
            'total_users': total_users,
        }
        
        serializer = UserProgressSerializer(data)
        return Response(serializer.data)


class UserActivityCalendarView(generics.GenericAPIView):
    """
    Get user activity for calendar heat map
    GET /api/users/activity-calendar/?days=365
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    serializer_class = UserActivitySerializer
    
    @extend_schema(
        responses=UserActivitySerializer(many=True),
        description='Get user activity for calendar heat map',
        summary='Get Activity Calendar'
    )
    def get(self, request):
        user = request.user
        days = int(request.query_params.get('days', 365))
        
        start_date = timezone.now().date() - timedelta(days=days)
        activities = UserActivity.objects.filter(
            user=user,
            date__gte=start_date
        ).order_by('date')
        
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)


class SolvedProblemsView(generics.ListAPIView):
    """
    Get list of solved problems
    GET /api/users/solved-problems/?difficulty=EASY
    """
    serializer_class = SolvedProblemSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_queryset(self):
        user = self.request.user
        queryset = ProblemSolveStatus.objects.filter(
            user=user,
            status='SOLVED'
        ).select_related('problem')
        
        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(problem__difficulty=difficulty.upper())
        
        return queryset.order_by('-first_solved_at')


class AttemptedProblemsView(generics.ListAPIView):
    """
    Get list of attempted (but not solved) problems
    GET /api/users/attempted-problems/
    """
    serializer_class = SolvedProblemSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_queryset(self):
        user = self.request.user
        return ProblemSolveStatus.objects.filter(
            user=user,
            status='ATTEMPTED'
        ).select_related('problem').order_by('-last_attempted_at')


class GlobalLeaderboardView(generics.ListAPIView):
    """
    Get global leaderboard
    GET /api/users/leaderboard/?limit=100
    """
    serializer_class = LeaderboardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        limit = int(self.request.query_params.get('limit', 100))
        
        # Get top users with rank
        users = User.objects.annotate(
            rank=Window(
                expression=RowNumber(),
                order_by=F('total_solved').desc()
            )
        ).filter(total_solved__gt=0).order_by('-total_solved')[:limit]
        
        return users


class UserPublicProfileView(generics.RetrieveAPIView):
    """
    Get public profile of any user
    GET /api/users/<username>/profile/
    """
    serializer_class = UserProfileStatsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'username'
    
    def get_queryset(self):
        return User.objects.filter(is_active=True, is_banned=False)


class MyProfileStatsView(generics.RetrieveAPIView):
    """
    Get current user's detailed profile
    GET /api/users/my-profile-stats/
    """
    serializer_class = UserProfileStatsSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_object(self):
        return self.request.user


class AchievementsListView(generics.ListAPIView):
    """
    Get all available achievements
    GET /api/achievements/
    """
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]


class UserAchievementsView(generics.GenericAPIView):
    """
    Get current user's earned achievements
    GET /api/users/my-achievements/
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    serializer_class = UserAchievementSerializer
    
    @extend_schema(
        responses=UserAchievementSerializer(many=True),
        description='Get current user earned achievements',
        summary='Get User Achievements'
    )
    def get(self, request):
        user_achievements = UserAchievement.objects.filter(
            user=request.user
        ).select_related('achievement')
        
        serializer = UserAchievementSerializer(user_achievements, many=True)
        return Response(serializer.data)


class CompareUsersView(generics.GenericAPIView):
    """
    Compare two users' statistics
    GET /api/users/compare/?user1=alice&user2=bob
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'user1': {'type': 'object'},
                    'user2': {'type': 'object'},
                }
            }
        },
        description='Compare two users statistics',
        summary='Compare Users'
    )
    def get(self, request):
        username1 = request.query_params.get('user1')
        username2 = request.query_params.get('user2')
        
        if not username1 or not username2:
            return Response(
                {'error': 'Both user1 and user2 parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user1 = User.objects.get(username=username1)
            user2 = User.objects.get(username=username2)
        except User.DoesNotExist:
            return Response(
                {'error': 'One or both users not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        def get_user_stats(user):
            submissions = Submission.objects.filter(user=user)
            total_subs = submissions.count()
            accepted = submissions.filter(verdict='ACCEPTED').count()
            
            return {
                'username': user.username,
                'total_solved': user.total_solved,
                'easy_solved': user.easy_solved,
                'medium_solved': user.medium_solved,
                'hard_solved': user.hard_solved,
                'total_submissions': total_subs,
                'acceptance_rate': round((accepted / total_subs * 100), 2) if total_subs > 0 else 0.0,
            }
        
        return Response({
            'user1': get_user_stats(user1),
            'user2': get_user_stats(user2),
        })