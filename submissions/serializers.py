from rest_framework import serializers
from .models import Submission, TestCaseResult
from problems.models import Problem


class SubmissionCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new submission
    """
    problem_slug = serializers.SlugField()
    code = serializers.CharField()
    language = serializers.ChoiceField(choices=Submission.Language.choices)
    
    def validate_problem_slug(self, value):
        """Check if problem exists"""
        try:
            Problem.objects.get(slug=value, is_active=True)
        except Problem.DoesNotExist:
            raise serializers.ValidationError("Problem not found or inactive")
        return value
    
    def validate_code(self, value):
        """Validate code is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Code cannot be empty")
        if len(value) > 50000:  # 50KB limit
            raise serializers.ValidationError("Code is too long (max 50KB)")
        return value


class TestCaseResultSerializer(serializers.ModelSerializer):
    """
    Serializer for test case results
    """
    test_case_order = serializers.IntegerField(source='test_case.order', read_only=True)
    test_case_type = serializers.CharField(source='test_case.test_type', read_only=True)
    input_data = serializers.SerializerMethodField()
    expected_output = serializers.SerializerMethodField()
    
    class Meta:
        model = TestCaseResult
        fields = [
            'id', 'test_case_order', 'test_case_type', 
            'status', 'input_data', 'expected_output',
            'actual_output', 'execution_time', 'memory_used',
            'error_message'
        ]
    
    def get_input_data(self, obj):
        """Show input only for sample test cases"""
        if obj.test_case.test_type == 'SAMPLE':
            return obj.test_case.input_data
        return None
    
    def get_expected_output(self, obj):
        """Show expected output only for sample test cases"""
        if obj.test_case.test_type == 'SAMPLE':
            return obj.test_case.expected_output
        return None


class SubmissionListSerializer(serializers.ModelSerializer):
    """
    Serializer for submission listing
    """
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_slug = serializers.CharField(source='problem.slug', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    pass_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Submission
        fields = [
            'id', 'problem_title', 'problem_slug', 'username',
            'language', 'verdict', 'execution_time', 'memory_used',
            'test_cases_passed', 'total_test_cases', 'pass_percentage',
            'submitted_at'
        ]


class SubmissionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for submission detail view
    """
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_slug = serializers.CharField(source='problem.slug', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    test_case_results = TestCaseResultSerializer(many=True, read_only=True)
    pass_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Submission
        fields = [
            'id', 'problem_title', 'problem_slug', 'username',
            'code', 'language', 'verdict', 
            'execution_time', 'memory_used',
            'test_cases_passed', 'total_test_cases', 'pass_percentage',
            'error_message', 'compilation_output',
            'test_case_results', 'submitted_at'
        ]


class UserSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for user's own submissions (includes code)
    """
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_slug = serializers.CharField(source='problem.slug', read_only=True)
    pass_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Submission
        fields = [
            'id', 'problem_title', 'problem_slug',
            'code', 'language', 'verdict',
            'execution_time', 'memory_used',
            'test_cases_passed', 'total_test_cases', 'pass_percentage',
            'error_message', 'compilation_output',
            'submitted_at'
        ]


class SubmissionStatsSerializer(serializers.Serializer):
    """
    Serializer for submission statistics
    """
    total_submissions = serializers.IntegerField()
    accepted = serializers.IntegerField()
    wrong_answer = serializers.IntegerField()
    time_limit_exceeded = serializers.IntegerField()
    runtime_error = serializers.IntegerField()
    compilation_error = serializers.IntegerField()
    acceptance_rate = serializers.FloatField()