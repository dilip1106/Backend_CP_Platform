from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Problem, TestCase, Tag, ProblemSolveStatus
from django.utils.text import slugify


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for Tag model
    """
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['id', 'slug']
    
    def create(self, validated_data):
        validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)


class TestCaseSerializer(serializers.ModelSerializer):
    """
    Serializer for TestCase model
    """
    class Meta:
        model = TestCase
        fields = ['id', 'test_type', 'input_data', 'expected_output', 'order', 'is_active']
        read_only_fields = ['id']


class TestCaseCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating test cases
    """
    class Meta:
        model = TestCase
        fields = ['test_type', 'input_data', 'expected_output', 'order']


class ProblemListSerializer(serializers.ModelSerializer):
    """
    Serializer for problem listing (brief view)
    """
    tags = TagSerializer(many=True, read_only=True)
    acceptance_rate = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Problem
        fields = [
            'id', 'title', 'slug', 'difficulty', 'tags',
            'total_submissions', 'acceptance_rate', 'total_solved',
            'status', 'created_at'
        ]
    
    @extend_schema_field(serializers.FloatField())
    def get_acceptance_rate(self, obj) -> float:
        """Get problem acceptance rate"""
        return obj.acceptance_rate
    
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_status(self, obj) -> str:
        """Get user's solve status for this problem"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                status = ProblemSolveStatus.objects.get(user=request.user, problem=obj)
                return status.status
            except ProblemSolveStatus.DoesNotExist:
                return None
        return None


class ProblemDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for problem detail view
    """
    tags = TagSerializer(many=True, read_only=True)
    sample_test_cases = serializers.SerializerMethodField()
    acceptance_rate = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Problem
        fields = [
            'id', 'title', 'slug', 'description', 'difficulty', 'tags',
            'constraints', 'input_format', 'output_format', 'examples',
            'time_limit', 'memory_limit', 'sample_test_cases',
            'total_submissions', 'accepted_submissions', 'acceptance_rate',
            'total_solved', 'created_by_username', 'status',
            'created_at', 'updated_at'
        ]
    
    @extend_schema_field(TestCaseSerializer(many=True))
    def get_sample_test_cases(self, obj):
        """Get only sample (visible) test cases"""
        sample_cases = obj.test_cases.filter(test_type='SAMPLE', is_active=True)
        return TestCaseSerializer(sample_cases, many=True).data
    
    @extend_schema_field(serializers.FloatField())
    def get_acceptance_rate(self, obj) -> float:
        """Get problem acceptance rate"""
        return obj.acceptance_rate
    
    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_status(self, obj):
        """Get user's solve status"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                status = ProblemSolveStatus.objects.get(user=request.user, problem=obj)
                return {
                    'status': status.status,
                    'first_solved_at': status.first_solved_at,
                    'last_attempted_at': status.last_attempted_at
                }
            except ProblemSolveStatus.DoesNotExist:
                return None
        return None


class ProblemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating problems
    """
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    test_cases = TestCaseCreateSerializer(many=True, write_only=True, required=False)
    
    class Meta:
        model = Problem
        fields = [
            'title', 'description', 'difficulty', 'tag_ids',
            'constraints', 'input_format', 'output_format', 'examples',
            'time_limit', 'memory_limit', 'test_cases', 'is_active'
        ]
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        test_cases_data = validated_data.pop('test_cases', [])
        
        # Generate slug from title
        validated_data['slug'] = slugify(validated_data['title'])
        
        # Create problem
        problem = Problem.objects.create(**validated_data)
        
        # Add tags
        if tag_ids:
            problem.tags.set(tag_ids)
        
        # Create test cases
        for test_case_data in test_cases_data:
            TestCase.objects.create(problem=problem, **test_case_data)
        
        return problem


class ProblemUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating problems
    """
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Problem
        fields = [
            'title', 'description', 'difficulty', 'tag_ids',
            'constraints', 'input_format', 'output_format', 'examples',
            'time_limit', 'memory_limit', 'is_active'
        ]
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Update slug if title changes
        if 'title' in validated_data:
            validated_data['slug'] = slugify(validated_data['title'])
        
        # Update problem fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        return instance


class ProblemStatisticsSerializer(serializers.ModelSerializer):
    """
    Serializer for problem statistics
    """
    acceptance_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Problem
        fields = [
            'id', 'title', 'total_submissions', 'accepted_submissions',
            'acceptance_rate', 'total_solved'
        ]
    
    @extend_schema_field(serializers.FloatField())
    def get_acceptance_rate(self, obj) -> float:
        """Get problem acceptance rate"""
        return obj.acceptance_rate