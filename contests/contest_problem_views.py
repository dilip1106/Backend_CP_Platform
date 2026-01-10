from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse

from accounts.permissions import IsNotBanned
from .models import Contest
from .contest_problem_models import ContestProblem, ContestTestCase
from .contest_problem_serializers import (
    ContestProblemListSerializer,
    ContestProblemDetailSerializer,
    ContestProblemCreateSerializer,
    ContestProblemUpdateSerializer,
    ContestProblemReorderSerializer,
    ContestTestCaseSerializer,
    ContestTestCaseCreateSerializer,
    ContestProblemStatsSerializer
)
from .permissions import IsContestManager


# ==================== Contest Problem CRUD (Manager Only) ====================

class ContestProblemsListView(generics.ListAPIView):
    """
    List all problems in a contest
    GET /api/contests/<slug>/problems/
    """
    serializer_class = ContestProblemListSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        contest = get_object_or_404(Contest, slug=slug, is_active=True)
        
        # Only show active problems during contest
        # Managers can see all problems
        if self.request.user == contest.manager:
            return ContestProblem.objects.filter(contest=contest).order_by('order')
        else:
            return ContestProblem.objects.filter(
                contest=contest,
                is_active=True
            ).order_by('order')


class ContestProblemDetailView(generics.RetrieveAPIView):
    """
    Get contest problem details
    GET /api/contests/<slug>/problems/<int:pk>/
    """
    serializer_class = ContestProblemDetailSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_object(self):
        slug = self.kwargs.get('slug')
        pk = self.kwargs.get('pk')
        contest = get_object_or_404(Contest, slug=slug, is_active=True)
        
        return get_object_or_404(
            ContestProblem,
            contest=contest,
            pk=pk,
            is_active=True
        )


class ContestProblemCreateView(generics.CreateAPIView):
    """
    Create a problem for contest (Manager only)
    POST /api/contests/<slug>/problems/create/
    """
    serializer_class = ContestProblemCreateSerializer
    permission_classes = [IsAuthenticated, IsContestManager]
    
    def perform_create(self, serializer):
        slug = self.kwargs.get('slug')
        contest = get_object_or_404(Contest, slug=slug)
        
        # Check if contest has started
        if contest.is_running or contest.is_ended:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                'Cannot add problems to a contest that has started or ended'
            )
        
        serializer.save(contest=contest, created_by=self.request.user)


class ContestProblemUpdateView(generics.UpdateAPIView):
    """
    Update a contest problem (Manager only)
    PUT/PATCH /api/contests/<slug>/problems/<int:pk>/update/
    """
    serializer_class = ContestProblemUpdateSerializer
    permission_classes = [IsAuthenticated, IsContestManager]
    
    def get_object(self):
        slug = self.kwargs.get('slug')
        pk = self.kwargs.get('pk')
        contest = get_object_or_404(Contest, slug=slug)
        
        # Check if contest has started
        if contest.is_running or contest.is_ended:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                'Cannot update problems in a contest that has started or ended'
            )
        
        return get_object_or_404(ContestProblem, contest=contest, pk=pk)


class ContestProblemDeleteView(generics.DestroyAPIView):
    """
    Delete a contest problem (Manager only)
    DELETE /api/contests/<slug>/problems/<int:pk>/delete/
    """
    permission_classes = [IsAuthenticated, IsContestManager]
    serializer_class = ContestProblemDetailSerializer  # Added for Swagger
    
    def get_object(self):
        slug = self.kwargs.get('slug')
        pk = self.kwargs.get('pk')
        contest = get_object_or_404(Contest, slug=slug)
        
        # Check if contest has started
        if contest.is_running or contest.is_ended:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                'Cannot delete problems from a contest that has started or ended'
            )
        
        return get_object_or_404(ContestProblem, contest=contest, pk=pk)
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()


class ReorderProblemsView(views.APIView):
    """
    Reorder problems in a contest (Manager only)
    POST /api/contests/<slug>/problems/reorder/
    Body: {
        "problem_orders": [
            {"problem_id": 1, "order": 0},
            {"problem_id": 2, "order": 1}
        ]
    }
    """
    permission_classes = [IsAuthenticated, IsContestManager]
    
    @extend_schema(
        request=ContestProblemReorderSerializer,
        responses={200: ContestProblemListSerializer(many=True)}
    )
    def post(self, request, slug):
        contest = get_object_or_404(Contest, slug=slug)
        
        # Check if contest has started
        if contest.is_running or contest.is_ended:
            return Response(
                {'error': 'Cannot reorder problems in a contest that has started or ended'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ContestProblemReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        problem_orders = serializer.validated_data['problem_orders']
        
        # Update problem orders
        for item in problem_orders:
            problem_id = item['problem_id']
            new_order = item['order']
            
            try:
                problem = ContestProblem.objects.get(
                    id=problem_id,
                    contest=contest
                )
                problem.order = new_order
                problem.save(update_fields=['order'])
            except ContestProblem.DoesNotExist:
                pass
        
        # Return updated problem list
        problems = ContestProblem.objects.filter(contest=contest).order_by('order')
        return Response(
            ContestProblemListSerializer(problems, many=True).data
        )


# ==================== Test Cases (Manager Only) ====================

class ContestProblemTestCasesView(generics.ListAPIView):
    """
    List test cases for a problem
    GET /api/contests/<slug>/problems/<int:pk>/test-cases/
    Managers see all, participants see only SAMPLE
    """
    serializer_class = ContestTestCaseSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        pk = self.kwargs.get('pk')
        contest = get_object_or_404(Contest, slug=slug)
        problem = get_object_or_404(ContestProblem, contest=contest, pk=pk)
        
        # Manager sees all test cases, others see only sample
        if self.request.user == contest.manager:
            return ContestTestCase.objects.filter(
                problem=problem,
                is_active=True
            ).order_by('order')
        else:
            return ContestTestCase.objects.filter(
                problem=problem,
                test_type='SAMPLE',
                is_active=True
            ).order_by('order')


class ContestTestCaseCreateView(generics.CreateAPIView):
    """
    Create test case for contest problem (Manager only)
    POST /api/contests/<slug>/problems/<int:pk>/test-cases/create/
    """
    serializer_class = ContestTestCaseCreateSerializer
    permission_classes = [IsAuthenticated, IsContestManager]
    
    def perform_create(self, serializer):
        slug = self.kwargs.get('slug')
        pk = self.kwargs.get('pk')
        contest = get_object_or_404(Contest, slug=slug)
        problem = get_object_or_404(ContestProblem, contest=contest, pk=pk)
        
        # Check if contest has started
        if contest.is_running or contest.is_ended:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                'Cannot add test cases to a contest that has started or ended'
            )
        
        serializer.save(problem=problem)


class ContestTestCaseUpdateView(generics.UpdateAPIView):
    """
    Update test case (Manager only)
    PUT/PATCH /api/contests/test-cases/<int:pk>/update/
    """
    queryset = ContestTestCase.objects.all()
    serializer_class = ContestTestCaseSerializer
    permission_classes = [IsAuthenticated, IsContestManager]
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        test_case = get_object_or_404(ContestTestCase, pk=pk)
        
        # Check if user is manager of the contest
        if test_case.problem.contest.manager != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not the manager of this contest')
        
        # Check if contest has started
        if test_case.problem.contest.is_running or test_case.problem.contest.is_ended:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                'Cannot update test cases in a contest that has started or ended'
            )
        
        return test_case


class ContestTestCaseDeleteView(generics.DestroyAPIView):
    """
    Delete test case (Manager only)
    DELETE /api/contests/test-cases/<int:pk>/delete/
    """
    queryset = ContestTestCase.objects.all()
    serializer_class = ContestTestCaseSerializer  # Added for Swagger
    permission_classes = [IsAuthenticated, IsContestManager]
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        test_case = get_object_or_404(ContestTestCase, pk=pk)
        
        # Check if user is manager of the contest
        if test_case.problem.contest.manager != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not the manager of this contest')
        
        # Check if contest has started
        if test_case.problem.contest.is_running or test_case.problem.contest.is_ended:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                'Cannot delete test cases from a contest that has started or ended'
            )
        
        return test_case
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()


# ==================== Statistics ====================

class ContestProblemStatsView(views.APIView):
    """
    Get statistics for all problems in contest (Manager only)
    GET /api/contests/<slug>/problems/stats/
    """
    permission_classes = [IsAuthenticated, IsContestManager]
    
    @extend_schema(
        responses={200: ContestProblemStatsSerializer(many=True)}
    )
    def get(self, request, slug):
        contest = get_object_or_404(Contest, slug=slug)
        problems = ContestProblem.objects.filter(contest=contest).order_by('order')
        
        serializer = ContestProblemStatsSerializer(problems, many=True)
        return Response(serializer.data)