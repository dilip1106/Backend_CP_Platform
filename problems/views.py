from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from accounts.permissions import IsSuperUser, IsSuperUserOrReadOnly, IsNotBanned

from .models import Problem, TestCase, Tag, ProblemSolveStatus
from .serializers import (
    ProblemListSerializer,
    ProblemDetailSerializer,
    ProblemCreateSerializer,
    ProblemUpdateSerializer,
    TagSerializer,
    TestCaseSerializer,
    TestCaseCreateSerializer,
    ProblemStatisticsSerializer
)


# ==================== Tag Views ====================

class TagListCreateView(generics.ListCreateAPIView):
    """
    List all tags or create a new tag (SuperUser only for creation)
    GET /api/problems/tags/
    POST /api/problems/tags/
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsSuperUserOrReadOnly]


class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a tag (SuperUser only for update/delete)
    GET /api/problems/tags/<id>/
    PUT/PATCH /api/problems/tags/<id>/
    DELETE /api/problems/tags/<id>/
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsSuperUserOrReadOnly]


# ==================== Problem Views ====================

class ProblemListView(generics.ListAPIView):
    """
    List all problems with filters
    GET /api/problems/?difficulty=EASY&tags=1,2&search=array&status=SOLVED
    """
    serializer_class = ProblemListSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_queryset(self):
        queryset = Problem.objects.filter(is_active=True).prefetch_related('tags')
        
        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty.upper())
        
        # Filter by tags
        tags = self.request.query_params.get('tags', None)
        if tags:
            tag_ids = [int(t) for t in tags.split(',') if t.isdigit()]
            queryset = queryset.filter(tags__id__in=tag_ids).distinct()
        
        # Filter by user status (SOLVED, ATTEMPTED)
        user_status = self.request.query_params.get('status', None)
        if user_status and self.request.user.is_authenticated:
            user_problem_ids = ProblemSolveStatus.objects.filter(
                user=self.request.user,
                status=user_status.upper()
            ).values_list('problem_id', flat=True)
            queryset = queryset.filter(id__in=user_problem_ids)
        
        # Search by title or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')


class ProblemDetailView(generics.RetrieveAPIView):
    """
    Get problem details
    GET /api/problems/<slug>/
    """
    queryset = Problem.objects.filter(is_active=True)
    serializer_class = ProblemDetailSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    lookup_field = 'slug'


class ProblemCreateView(generics.CreateAPIView):
    """
    Create a new problem (SuperUser only)
    POST /api/problems/create/
    """
    queryset = Problem.objects.all()
    serializer_class = ProblemCreateSerializer
    permission_classes = [IsSuperUser]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProblemUpdateView(generics.UpdateAPIView):
    """
    Update a problem (SuperUser only)
    PUT/PATCH /api/problems/<slug>/update/
    """
    queryset = Problem.objects.all()
    serializer_class = ProblemUpdateSerializer
    permission_classes = [IsSuperUser]
    lookup_field = 'slug'


class ProblemDeleteView(generics.DestroyAPIView):
    """
    Delete a problem (SuperUser only) - soft delete
    DELETE /api/problems/<slug>/delete/
    """
    queryset = Problem.objects.all()
    permission_classes = [IsSuperUser]
    lookup_field = 'slug'
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()


# ==================== Test Case Views ====================

class TestCaseListView(generics.ListAPIView):
    """
    List all test cases for a problem (SuperUser sees all, others see only SAMPLE)
    GET /api/problems/<slug>/test-cases/
    """
    serializer_class = TestCaseSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        problem = Problem.objects.get(slug=slug)
        
        if self.request.user.is_superuser_role:
            # SuperUser sees all test cases
            return TestCase.objects.filter(problem=problem, is_active=True)
        else:
            # Others see only sample test cases
            return TestCase.objects.filter(
                problem=problem,
                test_type='SAMPLE',
                is_active=True
            )


class TestCaseCreateView(generics.CreateAPIView):
    """
    Create a test case for a problem (SuperUser only)
    POST /api/problems/<slug>/test-cases/create/
    """
    serializer_class = TestCaseCreateSerializer
    permission_classes = [IsSuperUser]
    
    def perform_create(self, serializer):
        slug = self.kwargs.get('slug')
        problem = Problem.objects.get(slug=slug)
        serializer.save(problem=problem)


class TestCaseUpdateView(generics.UpdateAPIView):
    """
    Update a test case (SuperUser only)
    PUT/PATCH /api/problems/test-cases/<id>/update/
    """
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [IsSuperUser]


class TestCaseDeleteView(generics.DestroyAPIView):
    """
    Delete a test case (SuperUser only)
    DELETE /api/problems/test-cases/<id>/delete/
    """
    queryset = TestCase.objects.all()
    permission_classes = [IsSuperUser]
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()


# ==================== Statistics Views ====================

class ProblemStatisticsView(generics.RetrieveAPIView):
    """
    Get problem statistics
    GET /api/problems/<slug>/statistics/
    """
    queryset = Problem.objects.filter(is_active=True)
    serializer_class = ProblemStatisticsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'


class UserProblemStatsView(views.APIView):
    """
    Get current user's problem solving statistics
    GET /api/problems/my-stats/
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get(self, request):
        user = request.user
        
        # Get counts by difficulty
        solved_problems = ProblemSolveStatus.objects.filter(
            user=user,
            status='SOLVED'
        ).select_related('problem')
        
        easy_solved = solved_problems.filter(problem__difficulty='EASY').count()
        medium_solved = solved_problems.filter(problem__difficulty='MEDIUM').count()
        hard_solved = solved_problems.filter(problem__difficulty='HARD').count()
        total_solved = solved_problems.count()
        
        attempted_problems = ProblemSolveStatus.objects.filter(
            user=user,
            status='ATTEMPTED'
        ).count()
        
        return Response({
            'total_solved': total_solved,
            'easy_solved': easy_solved,
            'medium_solved': medium_solved,
            'hard_solved': hard_solved,
            'total_attempted': attempted_problems,
            'total_problems': Problem.objects.filter(is_active=True).count()
        })