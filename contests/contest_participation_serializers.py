from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .contest_submission_models import ContestSubmission, ContestParticipant, ProblemSolveStatus


class ContestSubmissionCreateSerializer(serializers.Serializer):
    """
    Serializer for creating contest submissions
    """
    problem_id = serializers.IntegerField()
    code = serializers.CharField()
    language = serializers.ChoiceField(choices=ContestSubmission.Language.choices)
    
    def validate_code(self, value):
        """Validate code is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Code cannot be empty")
        if len(value) > 50000:
            raise serializers.ValidationError("Code is too long (max 50KB)")
        return value


class ContestSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for contest submission (brief view)
    """
    username = serializers.CharField(source='user.username', read_only=True)
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_order = serializers.IntegerField(source='problem.order', read_only=True)
    pass_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ContestSubmission
        fields = [
            'id', 'username', 'problem_title', 'problem_order',
            'language', 'verdict', 'execution_time', 'memory_used',
            'test_cases_passed', 'total_test_cases', 'pass_percentage',
            'submitted_at'
        ]
    
    @extend_schema_field(serializers.FloatField())
    def get_pass_percentage(self, obj) -> float:
        """Get submission pass percentage"""
        return obj.pass_percentage


class ContestSubmissionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed contest submission view
    """
    username = serializers.CharField(source='user.username', read_only=True)
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    pass_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ContestSubmission
        fields = [
            'id', 'username', 'problem_title', 'code', 'language',
            'verdict', 'execution_time', 'memory_used',
            'test_cases_passed', 'total_test_cases', 'pass_percentage',
            'error_message', 'compilation_output', 'submitted_at'
        ]
    
    @extend_schema_field(serializers.FloatField())
    def get_pass_percentage(self, obj) -> float:
        """Get submission pass percentage"""
        return obj.pass_percentage


class ProblemSolveStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for problem solve status
    """
    problem_id = serializers.IntegerField(source='problem.id', read_only=True)
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_order = serializers.IntegerField(source='problem.order', read_only=True)
    
    class Meta:
        model = ProblemSolveStatus
        fields = [
            'problem_id', 'problem_title', 'problem_order',
            'status', 'score', 'attempts', 'wrong_attempts',
            'solve_time', 'first_solved_at'
        ]


class ContestParticipantSerializer(serializers.ModelSerializer):
    """
    Serializer for contest participant (leaderboard entry)
    """
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ContestParticipant
        fields = [
            'rank', 'username', 'total_score', 'problems_solved',
            'total_time', 'penalty_time', 'last_submission_time'
        ]


class ContestLeaderboardSerializer(serializers.ModelSerializer):
    """
    Detailed leaderboard with problem-wise status
    """
    username = serializers.CharField(source='user.username', read_only=True)
    problem_statuses = ProblemSolveStatusSerializer(many=True, read_only=True)
    
    class Meta:
        model = ContestParticipant
        fields = [
            'rank', 'username', 'total_score', 'problems_solved',
            'total_time', 'penalty_time', 'problem_statuses',
            'last_submission_time'
        ]


class MyContestDashboardSerializer(serializers.Serializer):
    """
    User's personal contest dashboard
    """
    participant_info = ContestParticipantSerializer()
    problem_statuses = ProblemSolveStatusSerializer(many=True)
    recent_submissions = ContestSubmissionSerializer(many=True)
    contest_status = serializers.CharField()
    time_remaining = serializers.DictField(required=False)