from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.shortcuts import get_object_or_404

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


class RunCodeView(views.APIView):
    """
    Run code against sample test cases only (no verdict saved)
    POST /api/submissions/run/
    Body: {
        "problem_slug": "two-sum",
        "code": "...",
        "language": "PYTHON"
    }
    
    Response: {
        "test_results": [
            {
                "test_case_id": 1,
                "test_order": 0,
                "input": "...",
                "expected_output": "...",
                "actual_output": "...",
                "status": "ACCEPTED|WRONG_ANSWER|RUNTIME_ERROR|TIME_LIMIT_EXCEEDED",
                "execution_time": 125,
                "memory_used": 5120,
                "error_message": ""
            }
        ],
        "compilation_error": null,
        "all_passed": true
    }
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    serializer_class = SubmissionCreateSerializer
    
    @extend_schema(
        request=SubmissionCreateSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'test_results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'test_case_id': {'type': 'integer'},
                                'test_order': {'type': 'integer'},
                                'input': {'type': 'string'},
                                'expected_output': {'type': 'string'},
                                'actual_output': {'type': 'string'},
                                'status': {'type': 'string'},
                                'execution_time': {'type': 'integer'},
                                'memory_used': {'type': 'integer'},
                                'error_message': {'type': 'string'}
                            }
                        }
                    },
                    'compilation_error': {'type': 'string', 'nullable': True},
                    'all_passed': {'type': 'boolean'}
                }
            },
            400: OpenApiResponse(description='Bad Request'),
            404: OpenApiResponse(description='Problem Not Found'),
        },
        description='Run code against sample test cases only. Verdict is not saved to database.',
        summary='Run Code (Sample Test Cases Only)'
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
        
        # Get only SAMPLE test cases
        test_cases = problem.test_cases.filter(
            is_active=True,
            test_type='SAMPLE'  # Only sample test cases
        ).order_by('order')
        
        if not test_cases.exists():
            return Response(
                {'error': 'No sample test cases available for this problem'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize Judge0 service
        judge0 = Judge0Service()
        
        # Execute code against each sample test case
        test_results = []
        compilation_error = None
        all_passed = True
        
        for test_case in test_cases:
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
                test_results.append({
                    'test_case_id': test_case.id,
                    'test_order': test_case.order,
                    'input': test_case.input_data,
                    'expected_output': test_case.expected_output,
                    'actual_output': '',
                    'status': 'RUNTIME_ERROR',
                    'execution_time': 0,
                    'memory_used': 0,
                    'error_message': 'Failed to execute code'
                })
                all_passed = False
                continue
            
            # Parse result
            parsed = judge0.parse_result(result)
            
            # Safely get output values
            stdout = parsed.get('stdout')
            actual_output = stdout.strip() if stdout else ''
            
            # Safely convert execution_time
            exec_time = 0
            try:
                time_val = parsed.get('execution_time')
                if time_val is not None:
                    if isinstance(time_val, str):
                        time_val = float(time_val.strip())
                    exec_time = int(float(time_val) * 1000)  # Convert to ms
            except (ValueError, TypeError):
                exec_time = 0
            
            # Safely convert memory_used
            memory_val = 0
            try:
                mem = parsed.get('memory_used')
                if mem is not None:
                    if isinstance(mem, str):
                        mem = float(mem.strip())
                    memory_val = int(float(mem))
            except (ValueError, TypeError):
                memory_val = 0
            
            # Get error details
            stderr = parsed.get('stderr')
            message = parsed.get('message')
            error_msg = (stderr if stderr else '') or (message if message else '')
            
            # Determine verdict
            verdict = parsed.get('verdict', 'INTERNAL_ERROR')
            
            if verdict == 'COMPILATION_ERROR':
                compile_output = parsed.get('compile_output')
                compilation_error = compile_output if compile_output else 'Compilation error occurred'
                all_passed = False
                # Add this test case result and break
                test_results.append({
                    'test_case_id': test_case.id,
                    'test_order': test_case.order,
                    'input': test_case.input_data,
                    'expected_output': test_case.expected_output,
                    'actual_output': '',
                    'status': 'COMPILATION_ERROR',
                    'execution_time': 0,
                    'memory_used': 0,
                    'error_message': 'Compilation error'
                })
                break  # Stop testing after compilation error
            
            # Map Judge0 verdict to our status
            if verdict == 'ACCEPTED':
                status_str = 'ACCEPTED'
            elif verdict == 'WRONG_ANSWER':
                status_str = 'WRONG_ANSWER'
                all_passed = False
            elif verdict == 'TIME_LIMIT_EXCEEDED':
                status_str = 'TIME_LIMIT_EXCEEDED'
                all_passed = False
            elif verdict == 'RUNTIME_ERROR':
                status_str = 'RUNTIME_ERROR'
                all_passed = False
            elif verdict == 'MEMORY_LIMIT_EXCEEDED':
                status_str = 'MEMORY_LIMIT_EXCEEDED'
                all_passed = False
            else:
                status_str = 'RUNTIME_ERROR'
                all_passed = False
            
            test_results.append({
                'test_case_id': test_case.id,
                'test_order': test_case.order,
                'input': test_case.input_data,
                'expected_output': test_case.expected_output,
                'actual_output': actual_output,
                'status': status_str,
                'execution_time': exec_time,
                'memory_used': memory_val,
                'error_message': error_msg
            })
        
        return Response({
            'test_results': test_results,
            'compilation_error': compilation_error,
            'all_passed': all_passed
        }, status=status.HTTP_200_OK)


class SubmissionCreateView(views.APIView):
    """
    Submit code for a problem (runs against all test cases and saves verdict)
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
        description='Submit code for a problem. The code will be executed against all test cases and verdict will be saved.',
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
        
        # Get all test cases (both SAMPLE and HIDDEN)
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
            
            # Update test case result - safely handle None values
            stdout = parsed.get('stdout')
            tc_result.actual_output = stdout.strip() if stdout else ''
            
            # Safely convert execution_time to integer (in milliseconds)
            try:
                exec_time = parsed.get('execution_time')
                if exec_time is not None:
                    # Handle both string and float types
                    if isinstance(exec_time, str):
                        exec_time = float(exec_time.strip())
                    tc_result.execution_time = int(float(exec_time) * 1000)  # Convert to ms
                else:
                    tc_result.execution_time = 0
            except (ValueError, TypeError):
                tc_result.execution_time = 0
            
            # Safely convert memory_used to integer
            try:
                memory = parsed.get('memory_used')
                if memory is not None:
                    if isinstance(memory, str):
                        memory = float(memory.strip())
                    tc_result.memory_used = int(float(memory))
                else:
                    tc_result.memory_used = 0
            except (ValueError, TypeError):
                tc_result.memory_used = 0
            
            # Safely get stderr and message
            stderr = parsed.get('stderr')
            message = parsed.get('message')
            tc_result.error_message = (stderr if stderr else '') or (message if message else '')
            
            # Determine status
            verdict = parsed.get('verdict', 'INTERNAL_ERROR')
            
            if verdict == 'ACCEPTED':
                tc_result.status = TestCaseResult.Status.ACCEPTED
                submission.test_cases_passed += 1
            elif verdict == 'WRONG_ANSWER':
                tc_result.status = TestCaseResult.Status.WRONG_ANSWER
                all_passed = False
            elif verdict == 'TIME_LIMIT_EXCEEDED':
                tc_result.status = TestCaseResult.Status.TIME_LIMIT_EXCEEDED
                all_passed = False
            elif verdict == 'RUNTIME_ERROR':
                tc_result.status = TestCaseResult.Status.RUNTIME_ERROR
                all_passed = False
            elif verdict == 'COMPILATION_ERROR':
                # Compilation error affects the whole submission
                submission.verdict = Submission.Verdict.COMPILATION_ERROR
                compile_output = parsed.get('compile_output')
                submission.compilation_output = compile_output if compile_output else ''
                submission.save()
                tc_result.status = TestCaseResult.Status.RUNTIME_ERROR
                tc_result.error_message = "Compilation error"
                tc_result.save()
                break
            
            tc_result.save()
            
            # Track max time and memory
            if tc_result.execution_time and tc_result.execution_time > max_time:
                max_time = tc_result.execution_time
            if tc_result.memory_used and tc_result.memory_used > max_memory:
                max_memory = tc_result.memory_used
        
        # Update submission verdict
        if submission.verdict != Submission.Verdict.COMPILATION_ERROR:
            if all_passed and submission.test_cases_passed > 0:
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
                else:
                    submission.verdict = Submission.Verdict.INTERNAL_ERROR
        
        submission.execution_time = max_time if max_time > 0 else None
        submission.memory_used = max_memory if max_memory > 0 else None
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
    GET /api/submissions/<pk>/
    """
    queryset = Submission.objects.all()
    serializer_class = SubmissionDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'


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