from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from accounts.permissions import IsNotBanned, IsSuperUser
from problems.models import Problem, ProblemSolveStatus
from .models import Submission, TestCaseResult
from .serializers import (
    SubmissionCreateSerializer,
    SubmissionListSerializer,
    SubmissionDetailSerializer,
    UserSubmissionSerializer,
    SubmissionStatsSerializer
)
from .judge0_service import Judge0Service


class SubmissionCreateView(views.APIView):
    """
    Submit code for a problem
    POST /api/submissions/submit/
    Body: {
        "problem_slug": "two-sum",
        "code": "...",
        "language": "PYTHON"
    }
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    serializer_class = SubmissionCreateSerializer  # Added for Swagger
    
    @extend_schema(
        request=SubmissionCreateSerializer,
        responses={
            201: SubmissionDetailSerializer,
            400: OpenApiResponse(description='Bad Request'),
            404: OpenApiResponse(description='Problem Not Found'),
        },
        description='Submit code for a problem. The code will be executed against all test cases.',
        summary='Submit Code Solution'
    )
    
    def post(self, request):
        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        problem_slug = serializer.validated_data['problem_slug']
        code = serializer.validated_data['code']
        language = serializer.validated_data['language']
        
        # Get problem
        try:
            problem = Problem.objects.get(slug=problem_slug, is_active=True)
        except Problem.DoesNotExist:
            return Response(
                {'error': 'Problem not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create submission
        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            code=code,
            language=language,
            verdict=Submission.Verdict.RUNNING
        )
        
        # Get all test cases
        test_cases = problem.test_cases.filter(is_active=True).order_by('order')
        submission.total_test_cases = test_cases.count()
        submission.save()
        
        # Initialize Judge0 service
        judge0 = Judge0Service()
        
        # Execute code against each test case
        all_passed = True
        max_time = 0
        max_memory = 0
        
        for test_case in test_cases:
            # Create test case result
            tc_result = TestCaseResult.objects.create(
                submission=submission,
                test_case=test_case,
                status=TestCaseResult.Status.PENDING
            )
            
            # Execute code
            result = judge0.execute_and_wait(
                source_code=code,
                language=language,
                stdin=test_case.input_data,
                expected_output=test_case.expected_output,
                time_limit=problem.time_limit / 1000.0,  # Convert ms to seconds
                memory_limit=problem.memory_limit * 1024  # Convert MB to KB
            )
            
            if not result:
                tc_result.status = TestCaseResult.Status.RUNTIME_ERROR
                tc_result.error_message = "Failed to execute code"
                tc_result.save()
                all_passed = False
                continue
            
            # Parse result
            parsed = judge0.parse_result(result)
            
            # Update test case result
            tc_result.actual_output = parsed['stdout'].strip()
            tc_result.execution_time = int((parsed['execution_time'] or 0) * 1000)  # Convert to ms
            tc_result.memory_used = parsed['memory_used'] or 0
            tc_result.error_message = parsed['stderr'] or parsed['message']
            
            # Determine status
            if parsed['verdict'] == 'ACCEPTED':
                tc_result.status = TestCaseResult.Status.ACCEPTED
                submission.test_cases_passed += 1
            elif parsed['verdict'] == 'WRONG_ANSWER':
                tc_result.status = TestCaseResult.Status.WRONG_ANSWER
                all_passed = False
            elif parsed['verdict'] == 'TIME_LIMIT_EXCEEDED':
                tc_result.status = TestCaseResult.Status.TIME_LIMIT_EXCEEDED
                all_passed = False
            elif parsed['verdict'] == 'RUNTIME_ERROR':
                tc_result.status = TestCaseResult.Status.RUNTIME_ERROR
                all_passed = False
            elif parsed['verdict'] == 'COMPILATION_ERROR':
                # Compilation error affects the whole submission
                submission.verdict = Submission.Verdict.COMPILATION_ERROR
                submission.compilation_output = parsed['compile_output']
                submission.save()
                tc_result.status = TestCaseResult.Status.RUNTIME_ERROR
                tc_result.error_message = "Compilation error"
                tc_result.save()
                break
            
            tc_result.save()
            
            # Track max time and memory
            if tc_result.execution_time:
                max_time = max(max_time, tc_result.execution_time)
            if tc_result.memory_used:
                max_memory = max(max_memory, tc_result.memory_used)
        
        # Update submission verdict
        if submission.verdict != Submission.Verdict.COMPILATION_ERROR:
            if all_passed:
                submission.verdict = Submission.Verdict.ACCEPTED
            else:
                # Find the first failure to determine verdict
                first_failure = submission.test_case_results.exclude(
                    status=TestCaseResult.Status.ACCEPTED
                ).first()
                
                if first_failure:
                    if first_failure.status == TestCaseResult.Status.WRONG_ANSWER:
                        submission.verdict = Submission.Verdict.WRONG_ANSWER
                    elif first_failure.status == TestCaseResult.Status.TIME_LIMIT_EXCEEDED:
                        submission.verdict = Submission.Verdict.TIME_LIMIT_EXCEEDED
                    elif first_failure.status == TestCaseResult.Status.RUNTIME_ERROR:
                        submission.verdict = Submission.Verdict.RUNTIME_ERROR
        
        submission.execution_time = max_time
        submission.memory_used = max_memory
        submission.save()
        
        # Update problem statistics
        problem.increment_submissions()
        if submission.is_accepted:
            problem.increment_accepted()
        
        # Update user's problem solve status
        self._update_user_status(request.user, problem, submission.is_accepted)
        
        # Return submission details
        return Response(
            SubmissionDetailSerializer(submission).data,
            status=status.HTTP_201_CREATED
        )
    
    def _update_user_status(self, user, problem, is_accepted):
        """Update user's solve status for the problem"""
        status_obj, created = ProblemSolveStatus.objects.get_or_create(
            user=user,
            problem=problem,
            defaults={'status': 'ATTEMPTED'}
        )
        
        if is_accepted and status_obj.status != 'SOLVED':
            status_obj.status = 'SOLVED'
            status_obj.first_solved_at = timezone.now()
            status_obj.save()
            
            # Increment problem's total_solved count
            problem.increment_solved()
            
            # Update user's statistics
            user.total_solved += 1
            if problem.difficulty == 'EASY':
                user.easy_solved += 1
            elif problem.difficulty == 'MEDIUM':
                user.medium_solved += 1
            elif problem.difficulty == 'HARD':
                user.hard_solved += 1
            user.save()


class SubmissionListView(generics.ListAPIView):
    """
    List all submissions (with filters)
    GET /api/submissions/?problem_slug=two-sum&verdict=ACCEPTED&language=PYTHON
    """
    serializer_class = SubmissionListSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='problem_slug',
                description='Filter by problem slug',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='verdict',
                description='Filter by verdict (ACCEPTED, WRONG_ANSWER, etc.)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='language',
                description='Filter by programming language',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='username',
                description='Filter by username',
                required=False,
                type=str
            ),
        ],
        description='List all submissions with optional filters',
        summary='List Submissions'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Submission.objects.select_related('user', 'problem')
        
        # Filter by problem
        problem_slug = self.request.query_params.get('problem_slug', None)
        if problem_slug:
            queryset = queryset.filter(problem__slug=problem_slug)
        
        # Filter by verdict
        verdict = self.request.query_params.get('verdict', None)
        if verdict:
            queryset = queryset.filter(verdict=verdict.upper())
        
        # Filter by language
        language = self.request.query_params.get('language', None)
        if language:
            queryset = queryset.filter(language=language.upper())
        
        # Filter by user
        username = self.request.query_params.get('username', None)
        if username:
            queryset = queryset.filter(user__username=username)
        
        return queryset.order_by('-submitted_at')


class SubmissionDetailView(generics.RetrieveAPIView):
    """
    Get submission details
    GET /api/submissions/<id>/
    """
    queryset = Submission.objects.all()
    serializer_class = SubmissionDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use UserSubmissionSerializer if viewing own submission"""
        submission = self.get_object()
        if self.request.user == submission.user:
            return UserSubmissionSerializer
        return SubmissionDetailSerializer


class MySubmissionsView(generics.ListAPIView):
    """
    Get current user's submissions
    GET /api/submissions/my-submissions/
    """
    serializer_class = UserSubmissionSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_queryset(self):
        return Submission.objects.filter(
            user=self.request.user
        ).select_related('problem').order_by('-submitted_at')


class MySubmissionStatsView(views.APIView):
    """
    Get current user's submission statistics
    GET /api/submissions/my-stats/
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    serializer_class = SubmissionStatsSerializer  # Added for Swagger
    
    @extend_schema(
        responses={200: SubmissionStatsSerializer},
        description='Get submission statistics for the current user',
        summary='Get User Submission Statistics'
    )
    def get(self, request):
        user = request.user
        submissions = Submission.objects.filter(user=user)
        
        stats = submissions.aggregate(
            total_submissions=Count('id'),
            accepted=Count('id', filter=Q(verdict='ACCEPTED')),
            wrong_answer=Count('id', filter=Q(verdict='WRONG_ANSWER')),
            time_limit_exceeded=Count('id', filter=Q(verdict='TIME_LIMIT_EXCEEDED')),
            runtime_error=Count('id', filter=Q(verdict='RUNTIME_ERROR')),
            compilation_error=Count('id', filter=Q(verdict='COMPILATION_ERROR')),
        )
        
        total = stats['total_submissions'] or 1
        stats['acceptance_rate'] = round((stats['accepted'] / total) * 100, 2)
        
        serializer = SubmissionStatsSerializer(stats)
        return Response(serializer.data)