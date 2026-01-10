from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .contest_problem_models import ContestProblem, ContestTestCase


class ContestTestCaseSerializer(serializers.ModelSerializer):
    """
    Serializer for contest test cases
    """
    class Meta:
        model = ContestTestCase
        fields = ['id', 'test_type', 'input_data', 'expected_output', 'order', 'is_active']
        read_only_fields = ['id']


class ContestTestCaseCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating contest test cases
    """
    class Meta:
        model = ContestTestCase
        fields = ['test_type', 'input_data', 'expected_output', 'order']


class ContestProblemListSerializer(serializers.ModelSerializer):
    """
    Serializer for contest problem listing
    """
    acceptance_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ContestProblem
        fields = [
            'id', 'title', 'difficulty', 'points', 'order',
            'total_submissions', 'acceptance_rate', 'total_solved',
            'time_limit', 'memory_limit'
        ]
    
    @extend_schema_field(serializers.FloatField)
    def get_acceptance_rate(self, obj):
        return obj.acceptance_rate


class ContestProblemDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for contest problem detail view
    """
    sample_test_cases = serializers.SerializerMethodField()
    acceptance_rate = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ContestProblem
        fields = [
            'id', 'title', 'description', 'difficulty', 'points',
            'constraints', 'input_format', 'output_format', 'examples',
            'time_limit', 'memory_limit', 'order',
            'sample_test_cases', 'total_submissions', 'accepted_submissions',
            'acceptance_rate', 'total_solved', 'created_by_username',
            'created_at', 'updated_at'
        ]
    
    @extend_schema_field(ContestTestCaseSerializer(many=True))
    def get_sample_test_cases(self, obj):
        """Get only sample (visible) test cases"""
        sample_cases = obj.test_cases.filter(test_type='SAMPLE', is_active=True)
        return ContestTestCaseSerializer(sample_cases, many=True).data
    
    @extend_schema_field(serializers.FloatField)
    def get_acceptance_rate(self, obj):
        return obj.acceptance_rate


class ContestProblemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating contest problems (Manager only)
    """
    test_cases = ContestTestCaseCreateSerializer(many=True, write_only=True, required=False)
    
    class Meta:
        model = ContestProblem
        fields = [
            'title', 'description', 'difficulty', 'points',
            'constraints', 'input_format', 'output_format', 'examples',
            'time_limit', 'memory_limit', 'order', 'test_cases'
        ]
    
    def create(self, validated_data):
        test_cases_data = validated_data.pop('test_cases', [])
        
        # Create problem
        problem = ContestProblem.objects.create(**validated_data)
        
        # Create test cases
        for test_case_data in test_cases_data:
            ContestTestCase.objects.create(problem=problem, **test_case_data)
        
        return problem


class ContestProblemUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating contest problems (Manager only)
    """
    class Meta:
        model = ContestProblem
        fields = [
            'title', 'description', 'difficulty', 'points',
            'constraints', 'input_format', 'output_format', 'examples',
            'time_limit', 'memory_limit', 'order', 'is_active'
        ]


class ContestProblemReorderSerializer(serializers.Serializer):
    """
    Serializer for reordering problems
    """
    problem_orders = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()),
        help_text='List of {problem_id: new_order}'
    )
    
    def validate_problem_orders(self, value):
        """Validate problem orders format"""
        for item in value:
            if 'problem_id' not in item or 'order' not in item:
                raise serializers.ValidationError(
                    'Each item must have problem_id and order'
                )
        return value


class ContestProblemStatsSerializer(serializers.ModelSerializer):
    """
    Serializer for problem statistics (Manager view)
    """
    acceptance_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ContestProblem
        fields = [
            'id', 'title', 'total_submissions', 'accepted_submissions',
            'acceptance_rate', 'total_solved'
        ]
    
    @extend_schema_field(serializers.FloatField)
    def get_acceptance_rate(self, obj):
        return obj.acceptance_rate