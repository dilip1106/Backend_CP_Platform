from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView,
    CustomTokenObtainPairView,
    UserProfileView,
    UserProfileUpdateView,
    ChangePasswordView,
    UserDetailView,
    UserListView,
    ChangeUserRoleView,
    BanUserView,
)

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Current User Profile
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    path('auth/profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # User Management (Public & Admin)
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/change-role/', ChangeUserRoleView.as_view(), name='change-role'),
    path('users/<int:pk>/<str:action>/', BanUserView.as_view(), name='ban-user'),
]