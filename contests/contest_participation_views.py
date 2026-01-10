from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Window, F
from django.db.models.functions import RowNumber
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsNotBanned
from .models import Contest, ContestRegistration
from .contest_problem_models import ContestProblem, ContestTestCase
from .contest_submission_models import ContestSubmission, ContestParticipant, ProblemSolveStatus
from .contest_participation_serializers import (
    ContestSubmissionCreateSerializer,
    ContestSubmissionSerializer,
    ContestSubmissionDetailSerializer,
    ContestParticipantSerializer,
    ContestLeaderboardSerializer,
    MyContestDashboardSerializer,
    ProblemSolveStatusSerializer
)
from submissions.judge0_service import Judge0Service


# ==================== Contest Submission ====================

class SubmitContestSolutionView(views.APIView):
    """
    Submit code for a contest problem
    POST /api/contests/<slug>/submit/
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    serializer_class = ContestSubmissionCreateSerializer  # Added for Swagger
    
    @extend_schema(
        request=ContestSubmissionCreateSerializer,
        responses={201: ContestSubmissionDetailSerializer}
    )
    def post(self, request, slug):
        contest = get_object_or_404(Contest, slug=slug, is_active=True)
        
        # Check if contest is running
        if not contest.is_running:
            return Response(
                {'error': 'Contest is not currently active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is registered
        if not ContestRegistration.objects.filter(user=request.user, contest=contest).exists():
            return Response(
                {'error': 'You are not registered for this contest'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ContestSubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        problem_id = serializer.validated_data['problem_id']
        code = serializer.validated_data['code']
        language = serializer.validated_data['language']
        
        # Get problem
        try:
            problem = ContestProblem.objects.get(
                id=problem_id,
                contest=contest,
                is_active=True
            )
        except ContestProblem.DoesNotExist:
            return Response(
                {'error': 'Problem not found in this contest'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create submission
        submission = ContestSubmission.objects.create(
            contest=contest,
            user=request.user,
            problem=problem,
            code=code,
            language=language,
            verdict=ContestSubmission.Verdict.RUNNING
        )
        
        # Get or create participant
        participant, _ = ContestParticipant.objects.get_or_create(
            contest=contest,
            user=request.user
        )
        
        # Get or create problem status
        problem_status, _ = ProblemSolveStatus.objects.get_or_create(
            participant=participant,
            problem=problem
        )
        
        # Increment attempts
        problem_status.attempts += 1
        problem_status.save()
        
        # Execute code against test cases
        test_cases = problem.test_cases.filter(is_active=True).order_by('order')
        submission.total_test_cases = test_cases.count()
        submission.save()
        
        judge0 = Judge0Service()
        
        all_passed = True
        max_time = 0
        max_memory = 0
        
        for test_case in test_cases:
            result = judge0.execute_and_wait(
                source_code=code,
                language=language,
                stdin=test_case.input_data,
                expected_output=test_case.expected_output,
                time_limit=problem.time_limit / 1000.0,
                memory_limit=problem.memory_limit * 1024
            )
            
            if not result:
                all_passed = False
                continue
            
            parsed = judge0.parse_result(result)
            
            if parsed['verdict'] == 'ACCEPTED':
                submission.test_cases_passed += 1
                if parsed['execution_time']:
                    max_time = max(max_time, int(parsed['execution_time'] * 1000))
                if parsed['memory_used']:
                    max_memory = max(max_memory, parsed['memory_used'])
            elif parsed['verdict'] == 'COMPILATION_ERROR':
                submission.verdict = ContestSubmission.Verdict.COMPILATION_ERROR
                submission.compilation_output = parsed.get('compile_output', '')
                submission.save()
                all_passed = False
                break
            else:
                all_passed = False
                if parsed['verdict'] == 'WRONG_ANSWER':
                    submission.verdict = ContestSubmission.Verdict.WRONG_ANSWER
                elif parsed['verdict'] == 'TIME_LIMIT_EXCEEDED':
                    submission.verdict = ContestSubmission.Verdict.TIME_LIMIT_EXCEEDED
                elif parsed['verdict'] == 'RUNTIME_ERROR':
                    submission.verdict = ContestSubmission.Verdict.RUNTIME_ERROR
                submission.error_message = parsed.get('stderr', '') or parsed.get('message', '')
        
        # Update submission verdict
        if submission.verdict != ContestSubmission.Verdict.COMPILATION_ERROR:
            if all_passed:
                submission.verdict = ContestSubmission.Verdict.ACCEPTED
                problem_status.status = 'SOLVED'
                problem_status.first_solved_at = timezone.now()
                problem_status.score = problem.points
                participant.problems_solved += 1
                participant.total_score += problem.points
            else:
                if submission.verdict == ContestSubmission.Verdict.WRONG_ANSWER:
                    pass
                submission.verdict = submission.verdict or ContestSubmission.Verdict.WRONG_ANSWER
        
        submission.execution_time = max_time if max_time > 0 else None
        submission.memory_used = max_memory if max_memory > 0 else None
        submission.save()
        
        problem_status.save()
        participant.total_time = (timezone.now() - contest.start_time).total_seconds() // 60
        participant.last_submission_time = timezone.now()
        participant.save()
        
        # Update rankings
        self._update_rankings(contest)
        
        return Response(
            ContestSubmissionDetailSerializer(submission).data,
            status=status.HTTP_201_CREATED
        )
    
    def _update_rankings(self, contest):
        """Update rankings for all participants"""
        participants = ContestParticipant.objects.filter(contest=contest).order_by(
            '-total_score', 'total_time'
        )
        for rank, participant in enumerate(participants, 1):
            participant.rank = rank
            participant.save()


# ==================== Leaderboard ====================

class ContestLeaderboardView(generics.ListAPIView):
    """
    Get contest leaderboard
    GET /api/contests/<slug>/leaderboard/
    """
    serializer_class = ContestParticipantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        contest = get_object_or_404(Contest, slug=slug, is_active=True)
        
        return ContestParticipant.objects.filter(
            contest=contest
        ).select_related('user').order_by('rank')


class DetailedLeaderboardView(generics.ListAPIView):
    """
    Get detailed leaderboard with problem-wise status
    GET /api/contests/<slug>/leaderboard/detailed/
    """
    serializer_class = ContestLeaderboardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        contest = get_object_or_404(Contest, slug=slug, is_active=True)
        
        return ContestParticipant.objects.filter(
            contest=contest
        ).select_related('user').prefetch_related('problem_statuses').order_by('rank')


# ==================== User Dashboard ====================

class MyContestDashboardView(generics.GenericAPIView):
    """
    Get user's contest dashboard with problems, statuses, and recent submissions
    GET /api/contests/<slug>/my-dashboard/
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    serializer_class = MyContestDashboardSerializer
    
    @extend_schema(
        responses={200: MyContestDashboardSerializer},
        description='Get user dashboard for a contest with problem statuses and recent submissions',
        summary='Get Contest Dashboard'
    )
    def get(self, request, slug):
        contest = get_object_or_404(Contest, slug=slug, is_active=True)
        
        # Check if user is registered
        if not ContestRegistration.objects.filter(user=request.user, contest=contest).exists():
            return Response(
                {'error': 'You are not registered for this contest'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create participant info
        participant, created = ContestParticipant.objects.get_or_create(
            contest=contest,
            user=request.user
        )
        
        # Get all contest problems
        contest_problems = contest.problems.filter(is_active=True).order_by('order')
        
        # Build problem statuses with their solve status
        problem_statuses_data = []
        for problem in contest_problems:
            problem_status = ProblemSolveStatus.objects.filter(
                participant=participant,
                problem=problem
            ).first()
            
            if problem_status:
                status_data = ProblemSolveStatusSerializer(problem_status).data
            else:
                # Initialize status for problems not attempted yet
                status_data = {
                    'problem_id': problem.id,
                    'problem_title': problem.title,
                    'problem_order': problem.order,
                    'status': None,
                    'score': 0,
                    'attempts': 0,
                    'wrong_attempts': 0,
                    'solve_time': None,
                    'first_solved_at': None
                }
            
            problem_statuses_data.append(status_data)
        
        # Get recent submissions (last 10)
        recent_submissions = ContestSubmission.objects.filter(
            contest=contest,
            user=request.user
        ).select_related('problem').order_by('-submitted_at')[:10]
        
        # Calculate time info
        time_info = {}
        now = timezone.now()
        
        if contest.start_time > now:
            time_until_start = contest.start_time - now
            time_info['status'] = 'UPCOMING'
            time_info['time_until_start'] = str(time_until_start)
            time_info['time_until_start_seconds'] = int(time_until_start.total_seconds())
        elif contest.end_time > now:
            time_remaining = contest.end_time - now
            elapsed = now - contest.start_time
            time_info['status'] = 'RUNNING'
            time_info['time_remaining'] = str(time_remaining)
            time_info['time_remaining_seconds'] = int(time_remaining.total_seconds())
            time_info['time_elapsed'] = str(elapsed)
            time_info['time_elapsed_seconds'] = int(elapsed.total_seconds())
        else:
            duration = contest.end_time - contest.start_time
            time_info['status'] = 'ENDED'
            time_info['total_duration'] = str(duration)
            time_info['total_duration_seconds'] = int(duration.total_seconds())
        
        data = {
            'participant_info': ContestParticipantSerializer(participant).data,
            'problem_statuses': problem_statuses_data,
            'recent_submissions': ContestSubmissionSerializer(recent_submissions, many=True).data,
            'contest_status': contest.status,
            'time_remaining': time_info
        }
        
        serializer = MyContestDashboardSerializer(data)
        return Response(serializer.data)


# ==================== Submissions History ====================

class MyContestSubmissionsView(generics.ListAPIView):
    """
    Get user's submissions for a contest
    GET /api/contests/<slug>/my-submissions/
    """
    serializer_class = ContestSubmissionSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        contest = get_object_or_404(Contest, slug=slug, is_active=True)
        
        return ContestSubmission.objects.filter(
            contest=contest,
            user=self.request.user
        ).select_related('problem').order_by('-submitted_at')


class ContestSubmissionDetailView(generics.RetrieveAPIView):
    """
    Get contest submission details
    GET /api/contests/submissions/<id>/
    """
    serializer_class = ContestSubmissionDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        submission = get_object_or_404(
            ContestSubmission,
            id=self.kwargs.get('pk')
        )
        
        # Users can only see their own submissions
        # Managers can see all submissions in their contest
        if submission.user != self.request.user:
            if submission.contest.manager != self.request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You can only view your own submissions')
        
        return submission