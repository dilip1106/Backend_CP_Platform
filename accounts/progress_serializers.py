from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.contrib.auth import get_user_model
from problems.models import ProblemSolveStatus
from submissions.models import Submission
from .additional_models import UserActivity, Achievement, UserAchievement

User = get_user_model()


class UserActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for user activity (heat map calendar)
    """
    class Meta:
        model = UserActivity
        fields = ['date', 'problems_solved', 'submissions_count']


class AchievementSerializer(serializers.ModelSerializer):
    """
    Serializer for achievements
    """
    class Meta:
        model = Achievement
        fields = ['id', 'name', 'description', 'achievement_type', 'icon']


class UserAchievementSerializer(serializers.ModelSerializer):
    """
    Serializer for user achievements
    """
    achievement = AchievementSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = ['achievement', 'earned_at']


class UserProgressSerializer(serializers.Serializer):
    """
    Comprehensive user progress statistics
    """
    # Basic stats
    total_solved = serializers.IntegerField()
    easy_solved = serializers.IntegerField()
    medium_solved = serializers.IntegerField()
    hard_solved = serializers.IntegerField()
    
    # Submission stats
    total_submissions = serializers.IntegerField()
    acceptance_rate = serializers.FloatField()
    
    # Problem status
    total_attempted = serializers.IntegerField()
    total_problems = serializers.IntegerField()
    
    # Rankings
    global_rank = serializers.IntegerField()
    total_users = serializers.IntegerField()


class RecentSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for recent submissions in activity feed
    """
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_slug = serializers.CharField(source='problem.slug', read_only=True)
    problem_difficulty = serializers.CharField(source='problem.difficulty', read_only=True)
    
    class Meta:
        model = Submission
        fields = [
            'id', 'problem_title', 'problem_slug', 'problem_difficulty',
            'verdict', 'language', 'submitted_at'
        ]


class SolvedProblemSerializer(serializers.ModelSerializer):
    """
    Serializer for solved problems list
    """
    problem_id = serializers.IntegerField(source='problem.id', read_only=True)
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_slug = serializers.CharField(source='problem.slug', read_only=True)
    problem_difficulty = serializers.CharField(source='problem.difficulty', read_only=True)
    
    class Meta:
        model = ProblemSolveStatus
        fields = [
            'problem_id', 'problem_title', 'problem_slug',
            'problem_difficulty', 'status', 'first_solved_at'
        ]


class LeaderboardSerializer(serializers.ModelSerializer):
    """
    Serializer for leaderboard
    """
    rank = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'rank', 'id', 'username', 'total_solved',
            'easy_solved', 'medium_solved', 'hard_solved'
        ]


class UserProfileStatsSerializer(serializers.ModelSerializer):
    """
    Enhanced user profile with all statistics
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    recent_submissions = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()
    solve_streak = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'bio', 'avatar', 'country',
            'total_solved', 'easy_solved', 'medium_solved', 'hard_solved',
            'date_joined', 'recent_submissions', 'recent_activity',
            'achievements', 'solve_streak'
        ]
    
    @extend_schema_field(RecentSubmissionSerializer(many=True))
    def get_recent_submissions(self, obj):
        """Get last 10 submissions"""
        submissions = Submission.objects.filter(user=obj).select_related('problem')[:10]
        return RecentSubmissionSerializer(submissions, many=True).data
    
    @extend_schema_field(UserActivitySerializer(many=True))
    def get_recent_activity(self, obj):
        """Get activity for last 30 days"""
        from datetime import timedelta
        from django.utils import timezone
        
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        activities = UserActivity.objects.filter(
            user=obj,
            date__gte=thirty_days_ago
        ).order_by('-date')
        return UserActivitySerializer(activities, many=True).data
    
    @extend_schema_field(UserAchievementSerializer(many=True))
    def get_achievements(self, obj):
        """Get earned achievements"""
        user_achievements = UserAchievement.objects.filter(user=obj).select_related('achievement')
        return UserAchievementSerializer(user_achievements, many=True).data
    
    @extend_schema_field(serializers.IntegerField())
    def get_solve_streak(self, obj) -> int:
        """Calculate current solve streak"""
        from datetime import timedelta
        from django.utils import timezone
        
        today = timezone.now().date()
        streak = 0
        current_date = today
        
        while True:
            activity = UserActivity.objects.filter(
                user=obj,
                date=current_date,
                problems_solved__gt=0
            ).first()
            
            if activity:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak