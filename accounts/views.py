from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.db.models import Q

from .serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    UserListSerializer,
    RoleChangeSerializer,
    BanActionSerializer
)
from .permissions import IsSuperUser, IsOwnerOrSuperUser, IsNotBanned

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'role': user.role,
            }
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view with user data
    POST /api/auth/login/
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserProfileView(generics.RetrieveAPIView):
    """
    Get current user profile
    GET /api/auth/profile/
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_object(self):
        return self.request.user


class UserProfileUpdateView(generics.UpdateAPIView):
    """
    Update current user profile
    PUT/PATCH /api/auth/profile/update/
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated, IsNotBanned]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Profile updated successfully',
            'user': UserDetailSerializer(instance).data
        })


class ChangePasswordView(views.APIView):
    """
    Change user password
    POST /api/auth/change-password/
    """
    permission_classes = [IsAuthenticated, IsNotBanned]
    serializer_class = ChangePasswordSerializer  # Added for Swagger
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class UserDetailView(generics.RetrieveAPIView):
    """
    Get user details by ID (public profile)
    GET /api/users/<id>/
    """
    queryset = User.objects.filter(is_active=True, is_banned=False)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    """
    List all users (SuperUser only)
    GET /api/users/?role=MANAGER&search=john
    """
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsSuperUser]
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by banned status
        is_banned = self.request.query_params.get('is_banned', None)
        if is_banned is not None:
            queryset = queryset.filter(is_banned=is_banned.lower() == 'true')
        
        # Search by username or email
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset.order_by('-date_joined')


class ChangeUserRoleView(views.APIView):
    """
    Change user role (SuperUser only)
    POST /api/users/<id>/change-role/
    Body: {"role": "MANAGER" or "NORMAL_USER"}
    """
    permission_classes = [IsSuperUser]
    serializer_class = RoleChangeSerializer  # Added for Swagger
    
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent changing own role
        if user.id == request.user.id:
            return Response(
                {'error': 'You cannot change your own role'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prevent changing other superusers
        if user.role == User.Role.SUPER_USER:
            return Response(
                {'error': 'Cannot change SuperUser role'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RoleChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user.role = serializer.validated_data['role']
        user.save(update_fields=['role'])
        
        return Response({
            'message': f'User role changed to {user.role}',
            'user': UserListSerializer(user).data
        })


class BanUserView(views.APIView):
    """
    Ban/Unban user (SuperUser only)
    POST /api/users/<id>/ban/
    POST /api/users/<id>/unban/
    """
    permission_classes = [IsSuperUser]
    serializer_class = BanActionSerializer  # Added for Swagger
    
    def post(self, request, pk, action):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent banning own account
        if user.id == request.user.id:
            return Response(
                {'error': 'You cannot ban yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prevent banning other superusers
        if user.role == User.Role.SUPER_USER:
            return Response(
                {'error': 'Cannot ban SuperUser'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if action == 'ban':
            user.ban_user()
            message = 'User banned successfully'
        elif action == 'unban':
            user.unban_user()
            message = 'User unbanned successfully'
        else:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': message,
            'user': UserListSerializer(user).data
        })